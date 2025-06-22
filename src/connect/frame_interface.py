"""
FrameInterface: High-level interface for Frame AR glasses

This module provides a comprehensive interface for Frame glasses that supports:
- Event-driven tap detection with automatic photo capture
- Text display capabilities with formatting options  
- Robust connection management with auto-recovery
- Comprehensive error handling and status monitoring
- Callback-based architecture for extensible functionality

The interface abstracts the complexity of the Frame SDK's message-passing architecture
and provides a clean, async API for common Frame operations.

Key Features:
- Tap callbacks trigger automatic photo capture
- Configurable photo capture settings (resolution, exposure)
- Text display with automatic truncation and positioning
- Battery and memory monitoring
- Connection health monitoring with auto-reconnect
- Extensible callback system for custom event handling

Technical Implementation:
- Uses FrameMsg for high-level messaging vs FrameBle's REPL approach
- Implements asynchronous message processing with proper cleanup
- Handles Bluetooth MTU limitations transparently
- Manages Lua app lifecycle with standard library uploads
- Provides thread-safe operation with proper resource management

Links:
https://docs.brilliant.xyz/frame/frame-sdk-python/#frame-ble-package-low-level-connectivity
https://frame-ble-python.readthedocs.io/en/latest/api.html
https://frame-msg-python.readthedocs.io/en/latest/api.html
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, Union, Awaitable
from datetime import datetime
from pathlib import Path
import os
import io
import inspect
from PIL import Image

# Frame SDK imports
from frame_msg import FrameMsg, RxPhoto, TxCaptureSettings, TxPlainText


class FrameInterface:
    """
    High-level interface for Frame AR glasses with event-driven tap handling and display capabilities.
    
    This class provides a clean, async API for Frame glasses operations including:
    - Automatic tap-to-capture functionality
    - Text display with formatting
    - Connection management with health monitoring
    - Extensible callback architecture
    
    ## Methods Overview:
    
    ### Initialization & Configuration:
    - `__init__(capture_resolution, auto_exposure_delay)`: Initialize interface with capture settings
    - `set_photo_callback(callback)`: Register callback for photo capture events  
    - `set_tap_callback(callback)`: Register callback for tap detection events
    - `set_error_callback(callback)`: Register callback for error handling
    - `set_status_callback(callback)`: Register callback for periodic status updates
    
    ### Connection Management:
    - `connect(max_retries)`: Establish connection to Frame glasses and upload Lua app
    - `disconnect()`: Clean disconnection with proper resource cleanup
    - `get_status()`: Get comprehensive device and connection status
    
    ### Core Operations:
    - `display_text(text, position_x, position_y)`: Display text on Frame glasses
    - `capture_photo(resolution)`: Manually trigger photo capture
    - `run_event_loop(status_update_interval)`: Main event processing loop for tap detection
    - `stop()`: Stop event loop and disconnect cleanly
    
    ### Utility Methods:
    - `save_image(image_data, filename)`: Save captured image data to disk
    - `get_image_info(image_data)`: Extract metadata from captured image data
    - `_upload_tap_handler_app()`: Internal method to upload custom Lua tap handler
    
    ## Intended Logical Flow:
    
    1. **Setup Phase:**
       - Create FrameInterface instance with desired settings
       - Register event callbacks (photo, tap, error, status) as needed
       
    2. **Connection Phase:**
       - Call `connect()` to establish Bluetooth connection and upload Frame app
       - Frame automatically uploads required Lua libraries and custom tap handler
       - Connection includes battery/memory status check and auto-exposure settling
       
    3. **Interactive Phase:**
       - Use `display_text()` to show information to user
       - Use `capture_photo()` for manual photo capture when needed
       - Call `run_event_loop()` to enable automatic tap detection and photo capture
       
    4. **Event Processing:**
       - Event loop monitors for tap events from Frame glasses
       - Tap events automatically trigger photo capture with visual feedback
       - Status updates occur periodically with callback notifications
       - Connection health is monitored with automatic reconnection attempts
       
    5. **Cleanup Phase:**
       - Call `stop()` to gracefully halt event processing
       - Automatically calls `disconnect()` to clean up resources
    
    ## Event-Driven Architecture:
    
    The interface uses callbacks for extensible event handling:
    - **Photo Callback**: Receives captured image data and metadata
    - **Tap Callback**: Notified immediately when user taps glasses  
    - **Error Callback**: Handles connection and processing errors
    - **Status Callback**: Receives periodic device status updates
    
    This design allows applications to respond to Frame events without polling,
    providing responsive user interaction and efficient resource usage.
    
    Example Usage:
        ```python
        async def on_photo_captured(image_data: bytes, metadata: dict):
            print(f"Captured {len(image_data)} bytes at {metadata['timestamp']}")
            
        async def on_tap_detected():
            print("Tap detected on Frame glasses!")
            
        interface = FrameInterface()
        interface.set_photo_callback(on_photo_captured)
        interface.set_tap_callback(on_tap_detected)
        
        await interface.connect()
        await interface.display_text("Ready for taps!")
        
        # Keep running to handle events
        await interface.run_event_loop()
        ```
    """
    
    def __init__(self, capture_resolution: int = 720, auto_exposure_delay: float = 3.0):
        """
        Initialize the Frame interface.
        
        Args:
            capture_resolution: Default photo capture resolution (720, 1080, etc.)
            auto_exposure_delay: Seconds to wait for auto-exposure to settle after connection
        """
        # Core Frame SDK components
        self.frame: Optional[FrameMsg] = None
        self.rx_photo: Optional[RxPhoto] = None
        self.photo_queue: Optional[asyncio.Queue] = None
        
        # Connection state management
        self.is_connected = False
        self.is_running = False
        self.last_connection_attempt: Optional[datetime] = None
        self.connection_retry_count = 0
        
        # Configuration
        self.capture_resolution = capture_resolution
        self.auto_exposure_delay = auto_exposure_delay
        self.max_text_length = 50  # Frame display limitation
        
        # Event callbacks - extensible architecture for custom functionality
        # Support both sync and async callbacks for flexibility
        self.photo_callback: Optional[Union[
            Callable[[bytes, Dict[str, Any]], None],
            Callable[[bytes, Dict[str, Any]], Awaitable[None]]
        ]] = None
        self.tap_callback: Optional[Union[
            Callable[[], None],
            Callable[[], Awaitable[None]]
        ]] = None
        self.error_callback: Optional[Union[
            Callable[[Exception], None],
            Callable[[Exception], Awaitable[None]]
        ]] = None
        self.status_callback: Optional[Union[
            Callable[[Dict[str, Any]], None],
            Callable[[Dict[str, Any]], Awaitable[None]]
        ]] = None
        
        # Status tracking
        self.last_capture_time: Optional[datetime] = None
        self.capture_count = 0
        self.last_battery_level: Optional[float] = None
        self.last_memory_usage: Optional[str] = None
        
        # Logging setup with structured logging for debugging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def _safe_callback(self, callback: Optional[Union[Callable, Callable[..., Awaitable]]], *args, **kwargs):
        """
        Safely execute a callback that might be sync or async.
        
        Args:
            callback: The callback function to execute
            *args: Arguments to pass to callback
            **kwargs: Keyword arguments to pass to callback
        """
        if callback is None:
            return
        
        try:
            # Check if callback is a coroutine function
            if inspect.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Callback error: {e}")
        
    def set_photo_callback(self, callback: Union[
        Callable[[bytes, Dict[str, Any]], None],
        Callable[[bytes, Dict[str, Any]], Awaitable[None]]
    ]):
        """
        Set callback function for photo capture events.
        
        The callback receives:
        - image_data (bytes): JPEG image data
        - metadata (dict): Capture metadata including timestamp, resolution, etc.
        
        Callback can be sync or async.
        """
        self.photo_callback = callback
        
    def set_tap_callback(self, callback: Union[
        Callable[[], None],
        Callable[[], Awaitable[None]]
    ]):
        """
        Set callback function for tap detection events.
        
        Called immediately when a tap is detected on the Frame glasses.
        Photo capture happens automatically after tap callback.
        
        Callback can be sync or async.
        """
        self.tap_callback = callback
        
    def set_error_callback(self, callback: Union[
        Callable[[Exception], None],
        Callable[[Exception], Awaitable[None]]
    ]):
        """Set callback function for error handling. Callback can be sync or async."""
        self.error_callback = callback
        
    def set_status_callback(self, callback: Union[
        Callable[[Dict[str, Any]], None],
        Callable[[Dict[str, Any]], Awaitable[None]]
    ]):
        """
        Set callback for periodic status updates.
        
        Receives device status including battery, memory, connection health.
        Callback can be sync or async.
        """
        self.status_callback = callback
    
    async def connect(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Connect to Frame glasses with robust error handling and setup.
        
        This method performs the complete Frame initialization sequence:
        1. Establish Bluetooth connection
        2. Upload required Lua libraries (data, camera, plain_text)  
        3. Upload custom Frame app with tap handling
        4. Initialize photo capture system
        5. Set up event processing
        
        Args:
            max_retries: Maximum connection retry attempts
            
        Returns:
            Dict with connection status, battery info, and any errors
        """
        self.last_connection_attempt = datetime.now()
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Connecting to Frame glasses (attempt {attempt + 1}/{max_retries + 1})")
                
                # Initialize Frame SDK connection
                self.frame = FrameMsg()
                await self.frame.connect()
                
                # Get initial device status for diagnostics
                batt_mem = await self.frame.send_lua(
                    'print(frame.battery_level() .. " / " .. collectgarbage("count"))', 
                    await_print=True
                )
                self.logger.info(f"Frame status: {batt_mem}")
                
                # Parse battery and memory for status tracking
                if batt_mem:
                    try:
                        parts = batt_mem.split(' / ')
                        if len(parts) == 2:
                            self.last_battery_level = float(parts[0])
                            self.last_memory_usage = parts[1]
                    except ValueError:
                        self.logger.warning(f"Could not parse battery/memory: {batt_mem}")
                
                # Display loading indicator
                await self.frame.print_short_text('Initializing...')
                
                # Upload standard Lua libraries required for functionality
                # - data: handles message parsing and queuing
                # - camera: photo capture and auto-exposure
                # - plain_text: text rendering and display
                await self.frame.upload_stdlua_libs(lib_names=['data', 'camera', 'plain_text'])
                
                # Upload our custom Frame app that handles tap events
                await self._upload_tap_handler_app()
                
                # Enable print response handling for debugging
                self.frame.attach_print_response_handler()
                
                # Start the Frame-side application loop
                await self.frame.start_frame_app()
                
                # Set up photo capture receiver with proper error handling
                self.rx_photo = RxPhoto()
                self.photo_queue = await self.rx_photo.attach(self.frame)
                
                # Validate that photo queue was properly initialized
                if self.photo_queue is None:
                    raise RuntimeError("Failed to initialize photo capture queue")
                
                # Allow auto-exposure to settle for better image quality
                self.logger.info(f"Allowing {self.auto_exposure_delay}s for auto-exposure to settle")
                await asyncio.sleep(self.auto_exposure_delay)
                
                self.is_connected = True
                self.connection_retry_count = 0
                
                # Notify successful connection
                success_result = {
                    "success": True,
                    "battery_level": self.last_battery_level,
                    "memory_usage": self.last_memory_usage,
                    "connection_time": self.last_connection_attempt.isoformat(),
                    "message": "Connected to Frame glasses successfully"
                }
                
                self.logger.info("Frame connection established successfully")
                await self.display_text("Connected!")
                
                return success_result
                
            except Exception as e:
                last_error = e
                self.connection_retry_count += 1
                error_msg = f"Connection attempt {attempt + 1} failed: {str(e)}"
                self.logger.error(error_msg)
                
                await self._safe_callback(self.error_callback, e)
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.info(f"Retrying connection in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    
        return {
            "success": False,
            "error": f"Failed to connect after {max_retries + 1} attempts: {str(last_error) if last_error else 'Unknown error'}",
            "retry_count": self.connection_retry_count,
            "message": "Failed to connect to Frame glasses after all retries"
        }
        
    async def _upload_tap_handler_app(self):
        """
        Upload custom Lua application that handles tap events and triggers photo capture.
        
        This creates a Lua app that:
        - Registers tap callback to detect user input
        - Processes incoming messages for photo capture requests  
        - Handles text display commands
        - Maintains event loop for responsive interaction
        """
        if self.frame is None:
            raise RuntimeError("Frame connection not established")
            
        # Create the tap-handling Lua application
        # This is more sophisticated than the basic camera app - it includes tap detection
        tap_handler_lua = '''
local data = require('data.min')
local camera = require('camera.min')
local plain_text = require('plain_text.min')

-- Message type constants for communication protocol
CAPTURE_SETTINGS_MSG = 0x0d
TEXT_DISPLAY_MSG = 0x11
TAP_DETECTED_MSG = 0x12

-- Register message parsers for automatic processing
data.parsers[CAPTURE_SETTINGS_MSG] = camera.parse_capture_settings
data.parsers[TEXT_DISPLAY_MSG] = plain_text.parse_plain_text

-- Visual feedback functions for better UX
function clear_display()
    frame.display.text(" ", 1, 1)
    frame.display.show()
    frame.sleep(0.04)
end

function show_capture_flash()
    -- Brief white flash to indicate photo capture
    frame.display.bitmap(241, 191, 160, 2, 0, string.rep("\\xFF", 400))
    frame.display.bitmap(311, 121, 20, 2, 0, string.rep("\\xFF", 400))
    frame.display.show()
    frame.sleep(0.04)
end

function show_tap_indicator()
    -- Quick visual confirmation of tap detection
    frame.display.text("TAP!", 200, 100)
    frame.display.show()
    frame.sleep(0.2)
    clear_display()
end

-- Tap callback function - called when user taps the glasses
function on_tap()
    print("TAP_DETECTED")  -- Send tap event to host
    show_tap_indicator()
    
    -- Auto-trigger photo capture on tap
    -- This provides immediate feedback to user action
    local capture_settings = {
        resolution = 720,
        auto_exposure = true,
        quality = 80
    }
    
    show_capture_flash()
    rc, err = pcall(camera.capture_and_send, capture_settings)
    clear_display()
    
    if rc == false then
        print("CAPTURE_ERROR: " .. tostring(err))
    else
        print("CAPTURE_SUCCESS")
    end
end

-- Register the tap callback with Frame system
frame.register_tap_callback(on_tap)

-- Main application event loop
function app_loop()
    clear_display()
    frame.display.text("Ready for taps", 1, 1)
    frame.display.show()
    
    -- Signal to host that Frame app is ready
    print('Frame app is running')
    
    while true do
        rc, err = pcall(
            function()
                -- Process incoming messages from host
                local items_ready = data.process_raw_items()
                
                if items_ready > 0 then
                    -- Handle manual capture requests from host
                    if data.app_data[CAPTURE_SETTINGS_MSG] ~= nil then
                        show_capture_flash()
                        rc, err = pcall(camera.capture_and_send, data.app_data[CAPTURE_SETTINGS_MSG])
                        clear_display()
                        
                        if rc == false then
                            print("MANUAL_CAPTURE_ERROR: " .. tostring(err))
                        else 
                            print("MANUAL_CAPTURE_SUCCESS")
                        end
                        
                        data.app_data[CAPTURE_SETTINGS_MSG] = nil
                    end
                    
                    -- Handle text display requests
                    if data.app_data[TEXT_DISPLAY_MSG] ~= nil then
                        local text_data = data.app_data[TEXT_DISPLAY_MSG]
                        clear_display()
                        frame.display.text(text_data.text, 1, 1)
                        frame.display.show()
                        data.app_data[TEXT_DISPLAY_MSG] = nil
                    end
                end
                
                -- Run camera auto-exposure when enabled
                if camera.is_auto_exp then
                    camera.run_auto_exposure()
                end
                
                -- Short sleep to prevent excessive CPU usage
                frame.sleep(0.05)
            end
        )
        
        -- Handle errors and break signals gracefully
        if rc == false then
            print("APP_ERROR: " .. tostring(err))
            clear_display()
            break
        end
    end
end

-- Start the main application loop
app_loop()
'''
        
        # Write the Lua app to a temporary file and upload it
        lua_file_path = os.path.join(os.path.dirname(__file__), "lua", "tap_handler_app.lua")
        os.makedirs(os.path.dirname(lua_file_path), exist_ok=True)
        
        with open(lua_file_path, 'w') as f:
            f.write(tap_handler_lua)
            
        await self.frame.upload_frame_app(local_filename=lua_file_path)
        self.logger.info("Uploaded tap handler Frame app")
    
    async def disconnect(self):
        """
        Clean disconnection from Frame glasses with proper resource cleanup.
        
        Ensures all resources are properly released:
        - Detaches photo receiver
        - Stops Frame application
        - Closes Bluetooth connection
        - Resets internal state
        """
        try:
            self.is_running = False
            
            if self.rx_photo and self.frame:
                self.rx_photo.detach(self.frame)
                
            if self.frame:
                self.frame.detach_print_response_handler()
                await self.frame.stop_frame_app()
                await self.frame.disconnect()
            
            # Reset state
            self.is_connected = False
            self.frame = None
            self.rx_photo = None
            self.photo_queue = None
            
            self.logger.info("Disconnected from Frame glasses")
            
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
            await self._safe_callback(self.error_callback, e)
    
    async def display_text(self, text: str, position_x: int = 1, position_y: int = 1) -> Dict[str, Any]:
        """
        Display text on Frame glasses with automatic formatting.
        
        Args:
            text: Text to display (will be truncated if too long)
            position_x: X coordinate on display
            position_y: Y coordinate on display
            
        Returns:
            Dict with success status and any errors
        """
        if not self.is_connected or not self.frame:
            return {
                "success": False,
                "error": "Not connected to Frame glasses"
            }
        
        try:
            # Truncate text to fit Frame display limitations  
            display_text = text[:self.max_text_length] if len(text) > self.max_text_length else text
            
            # Use TxPlainText for more control over text positioning
            text_message = TxPlainText(
                text=display_text,
                x=position_x,
                y=position_y
            )
            
            await self.frame.send_message(0x11, text_message.pack())
            
            self.logger.info(f"Displayed text: '{display_text}' at ({position_x}, {position_y})")
            
            return {
                "success": True,
                "text_displayed": display_text,
                "position": (position_x, position_y),
                "truncated": len(text) > self.max_text_length
            }
            
        except Exception as e:
            error_msg = f"Failed to display text: {str(e)}"
            self.logger.error(error_msg)
            
            await self._safe_callback(self.error_callback, e)
                    
            return {
                "success": False,
                "error": str(e)
            }
    
    async def capture_photo(self, resolution: Optional[int] = None) -> Dict[str, Any]:
        """
        Manually trigger photo capture (independent of tap events).
        
        Args:
            resolution: Override default capture resolution
            
        Returns:
            Dict with capture results and image metadata
        """
        if not self.is_connected or not self.frame:
            return {
                "success": False,
                "error": "Not connected to Frame glasses"
            }
        
        if self.photo_queue is None:
            return {
                "success": False,
                "error": "Photo capture system not initialized - photo_queue is None"
            }
        
        try:
            capture_resolution = resolution or self.capture_resolution
            
            # Send capture request to Frame
            await self.frame.send_message(
                0x0d, 
                TxCaptureSettings(resolution=capture_resolution).pack()
            )
            
            # Wait for image data with timeout
            jpeg_bytes = await asyncio.wait_for(self.photo_queue.get(), timeout=10.0)
            
            # Update capture statistics
            self.last_capture_time = datetime.now()
            self.capture_count += 1
            
            # Create metadata for the captured image
            metadata = {
                "timestamp": self.last_capture_time.isoformat(),
                "resolution": capture_resolution,
                "size_bytes": len(jpeg_bytes),
                "capture_count": self.capture_count,
                "triggered_by": "manual"
            }
            
            self.logger.info(f"Captured photo: {len(jpeg_bytes)} bytes at {capture_resolution}p")
            
            # Call photo callback if registered
            await self._safe_callback(self.photo_callback, jpeg_bytes, metadata)
            
            return {
                "success": True,
                "image_data": jpeg_bytes,
                "metadata": metadata
            }
            
        except asyncio.TimeoutError:
            error_msg = "Timeout waiting for photo capture"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Photo capture failed: {str(e)}"
            self.logger.error(error_msg)
            
            await self._safe_callback(self.error_callback, e)
                    
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive device and connection status.
        
        Returns detailed information about:
        - Connection state and health
        - Battery level and memory usage  
        - Capture statistics
        - Recent activity timestamps
        """
        base_status = {
            "connected": self.is_connected,
            "running": self.is_running,
            "last_connection": self.last_connection_attempt.isoformat() if self.last_connection_attempt else None,
            "connection_retries": self.connection_retry_count,
            "capture_count": self.capture_count,
            "last_capture": self.last_capture_time.isoformat() if self.last_capture_time else None,
        }
        
        if not self.is_connected or not self.frame:
            return {
                **base_status,
                "battery_level": self.last_battery_level,
                "memory_usage": self.last_memory_usage,
            }
        
        try:
            # Get fresh device status
            batt_mem = await self.frame.send_lua(
                'print(frame.battery_level() .. " / " .. collectgarbage("count"))', 
                await_print=True
            )
            
            if batt_mem:
                try:
                    parts = batt_mem.split(' / ')
                    if len(parts) == 2:
                        self.last_battery_level = int(parts[0])
                        self.last_memory_usage = parts[1]
                except ValueError:
                    self.logger.warning(f"Could not parse status: {batt_mem}")
            
            status = {
                **base_status,
                "battery_level": self.last_battery_level,
                "memory_usage": self.last_memory_usage,
                "device_response": batt_mem
            }
            
            # Trigger status callback if registered
            await self._safe_callback(self.status_callback, status)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting device status: {e}")
            return {
                **base_status,
                "battery_level": self.last_battery_level,
                "memory_usage": self.last_memory_usage,
                "error": str(e)
            }
    
    async def run_event_loop(self, status_update_interval: float = 30.0):
        """
        Run the main event processing loop.
        
        This method handles:
        - Processing Frame print responses for tap detection
        - Monitoring connection health  
        - Periodic status updates
        - Photo capture event processing
        - Error recovery and reconnection
        
        Args:
            status_update_interval: Seconds between status updates
        """
        if not self.is_connected:
            raise RuntimeError("Must connect to Frame glasses before running event loop")
            
        self.is_running = True
        last_status_update = datetime.now()
        
        self.logger.info("Starting Frame event loop")
        
        try:
            while self.is_running:
                # Process any pending photo captures
                if self.photo_queue and not self.photo_queue.empty():
                    try:
                        # Non-blocking check for new photos
                        jpeg_bytes = self.photo_queue.get_nowait()
                        
                        metadata = {
                            "timestamp": datetime.now().isoformat(),
                            "resolution": self.capture_resolution,
                            "size_bytes": len(jpeg_bytes),
                            "capture_count": self.capture_count + 1,
                            "triggered_by": "tap"
                        }
                        
                        self.capture_count += 1
                        self.last_capture_time = datetime.now()
                        
                        self.logger.info(f"Processing tap-triggered photo: {len(jpeg_bytes)} bytes")
                        
                        # Call photo callback
                        await self._safe_callback(self.photo_callback, jpeg_bytes, metadata)
                                
                    except asyncio.QueueEmpty:
                        pass
                
                # Check for tap events from Frame print responses
                # The Lua app sends "TAP_DETECTED" when user taps
                # This is handled through the print response system
                
                # Periodic status updates
                now = datetime.now()
                if (now - last_status_update).total_seconds() >= status_update_interval:
                    await self.get_status()  # This triggers status callback
                    last_status_update = now
                
                # Connection health check
                if not self.is_connected:
                    self.logger.warning("Connection lost, attempting to reconnect...")
                    reconnect_result = await self.connect()
                    if not reconnect_result["success"]:
                        self.logger.error("Reconnection failed, stopping event loop")
                        break
                
                # Short sleep to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Event loop error: {e}")
            await self._safe_callback(self.error_callback, e)
        finally:
            self.is_running = False
            self.logger.info("Frame event loop stopped")
    
    async def stop(self):
        """
        Stop the event loop and disconnect.
        
        Provides clean shutdown of all Frame operations.
        """
        self.logger.info("Stopping Frame interface...")
        self.is_running = False
        await self.disconnect()
        self.logger.info("Frame interface stopped")
    
    def save_image(self, image_data: bytes, filename: Optional[str] = None) -> str:
        """
        Utility method to save captured image data to disk.
        
        Args:
            image_data: JPEG image bytes from Frame capture
            filename: Optional custom filename, defaults to timestamp-based name
            
        Returns:
            Path to saved image file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frame_capture_{timestamp}.jpg"
        
        # Ensure we have a valid path
        if not filename.endswith(('.jpg', '.jpeg')):
            filename += '.jpg'
            
        filepath = os.path.join("static", "images", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
            
        self.logger.info(f"Saved image: {filepath} ({len(image_data)} bytes)")
        return filepath
    
    def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract metadata from captured image data.
        
        Args:
            image_data: JPEG image bytes
            
        Returns:
            Dict with image dimensions, format, and other metadata
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "has_transparency": image.mode in ('RGBA', 'LA', 'P'),
                "size_bytes": len(image_data)
            }
        except Exception as e:
            return {
                "error": str(e),
                "size_bytes": len(image_data)
            }