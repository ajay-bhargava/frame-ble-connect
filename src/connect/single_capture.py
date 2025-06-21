import asyncio
from PIL import Image
import io
import cv2
import numpy as np
import threading
import queue
import os
import sys
import requests  # Add this import at the top

from frame_msg import FrameMsg, RxPhoto, TxCaptureSettings

class ImageDisplayThread:
    def __init__(self, window_name="Camera Feed"):
        self.window_name = window_name
        self.image_queue = queue.Queue(maxsize=1)
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.display_available = True
        
    def start(self):
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        try:
            cv2.destroyAllWindows()
        except:
            pass
        
    def update_image(self, jpeg_bytes):
        if not self.display_available:
            return
        try:
            # Replace old image with new one
            if self.image_queue.full():
                try:
                    self.image_queue.get_nowait()
                except queue.Empty:
                    pass
            self.image_queue.put_nowait(jpeg_bytes)
        except queue.Full:
            pass  # Skip frame if queue is full
    
    def run(self):
        try:
            # Set environment variable for macOS
            if sys.platform == "darwin":
                os.environ['QT_QPA_PLATFORM'] = 'cocoa'
            
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        except Exception as e:
            print(f"Warning: Could not create OpenCV window: {e}")
            print("Running in headless mode - images will be captured but not displayed")
            self.display_available = False
            return
        
        while self.running:
            try:
                # Check if there's a new image
                try:
                    jpeg_bytes = self.image_queue.get(timeout=0.1)
                    
                    # Convert PIL Image to OpenCV format
                    pil_image = Image.open(io.BytesIO(jpeg_bytes))
                    cv_image = np.array(pil_image)
                    # Convert RGB to BGR (OpenCV uses BGR)
                    if cv_image.shape[2] == 3:  # If it has 3 channels
                        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
                    
                    # Display image
                    cv2.imshow(self.window_name, cv_image)
                except queue.Empty:
                    pass
                
                # Process events and check for key press
                key = cv2.waitKey(10) & 0xFF
                if key == 27:  # ESC key
                    self.running = False
                    break
                    
            except Exception as e:
                print(f"Error in display thread: {e}")
                break

async def main():
    """
    Take a single photo using the Frame camera, save it to disk, and display it briefly
    """
    frame = None
    display_thread = None
    rx_photo = None
    
    try:
        # Initialize display thread
        display_thread = ImageDisplayThread()
        display_thread.start()
        
        frame = FrameMsg()
        await frame.connect()

        # debug only: check our current battery level and memory usage
        batt_mem = await frame.send_lua('print(frame.battery_level() .. " / " .. collectgarbage("count"))', await_print=True)
        print(f"Battery Level/Memory used: {batt_mem}")

        # Let the user know we're starting
        await frame.print_short_text('Loading...')

        # send the std lua files to Frame
        await frame.upload_stdlua_libs(lib_names=['data', 'camera'])

        # Send the main lua application - use absolute path
        lua_file_path = os.path.join(os.path.dirname(__file__), "lua", "camera_frame_app.lua")
        await frame.upload_frame_app(local_filename=lua_file_path)

        frame.attach_print_response_handler()

        # Start the frame app
        await frame.start_frame_app()

        # hook up the RxPhoto receiver
        rx_photo = RxPhoto()
        photo_queue = await rx_photo.attach(frame)

        # give the frame some time for the autoexposure loop to run
        print("Letting autoexposure loop run for 5 seconds to settle")
        await asyncio.sleep(5.0)
        print("Starting capture")

        # Capture a single photo and save it
        print("Capturing photo...")
        await frame.send_message(0x0d, TxCaptureSettings(resolution=720).pack())
        
        # get the jpeg bytes
        jpeg_bytes = await asyncio.wait_for(photo_queue.get(), timeout=10.0)
        
        # Save the image to disk
        filename = "captured_frame.jpg"
        with open(filename, "wb") as f:
            f.write(jpeg_bytes)
        
        print(f"Image saved as {filename}")
        
        # --- New: Upload to API and print response ---
        api_url = "http://localhost:8000/api/v1/analysis/food-to-restaurant"
        try:
            with open(filename, "rb") as img_file:
                files = {"image": (filename, img_file, "image/jpeg")}
                response = requests.post(api_url, files=files)
            print("\nAPI response:")
            print(response.status_code, response.text)
        except Exception as e:
            print(f"Error uploading image to API: {e}")
        # --- End new code ---
        
        # Also update the display to show the captured image
        display_thread.update_image(jpeg_bytes)
        
        # Wait a moment to see the image, then exit
        await asyncio.sleep(2.0)
        
    except asyncio.CancelledError:
        print("\nCapture cancelled")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Clean up resources
        print("\nCleaning up resources...")
        if rx_photo and frame:
            rx_photo.detach(frame)
        if frame:
            frame.detach_print_response_handler()
            await frame.stop_frame_app()
            await frame.disconnect()
        if display_thread:
            display_thread.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")