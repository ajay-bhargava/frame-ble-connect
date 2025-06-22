#!/usr/bin/env python3
"""
Frame Interface Usage Example

This script demonstrates practical usage of the FrameInterface class
for AR glasses interaction with tap-to-capture and text display.

Features demonstrated:
- Connection management with error handling
- Event-driven tap detection and photo capture
- Text display with user feedback
- Status monitoring and logging
- Graceful shutdown handling

Usage:
    python example_frame_usage.py

Requirements:
    - Frame glasses paired and available
    - frame-msg and frame-ble packages installed
    - Proper Bluetooth permissions on system
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project paths for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "connect"))

from src.connect.frame_interface import FrameInterface


class FramePhotoApp:
    """
    Example application using FrameInterface for photo capture.
    
    This app demonstrates:
    - Setting up Frame connection with retry logic
    - Handling tap events for photo capture
    - Providing visual feedback to user
    - Saving captured images with metadata
    - Monitoring device status
    """
    
    def __init__(self):
        self.interface = FrameInterface(
            capture_resolution=720,  # Good balance of quality and speed
            auto_exposure_delay=3.0  # Allow camera to settle
        )
        
        self.running = True
        self.photo_count = 0
        self.save_directory = Path("captured_photos")
        self.save_directory.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('frame_app.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def on_photo_captured(self, image_data: bytes, metadata: dict):
        """
        Handle photo capture events with comprehensive processing.
        
        Args:
            image_data: JPEG image bytes from Frame
            metadata: Capture metadata including timestamp, resolution, etc.
        """
        self.photo_count += 1
        
        # Generate filename with timestamp and sequence
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"frame_photo_{timestamp}_{self.photo_count:03d}.jpg"
        filepath = self.save_directory / filename
        
        # Save the image
        try:
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            self.logger.info(f"📸 Photo {self.photo_count} saved: {filepath}")
            self.logger.info(f"   Size: {len(image_data):,} bytes")
            self.logger.info(f"   Resolution: {metadata['resolution']}p")
            self.logger.info(f"   Triggered by: {metadata['triggered_by']}")
            
            # Get detailed image information
            image_info = self.interface.get_image_info(image_data)
            if "error" not in image_info:
                self.logger.info(f"   Dimensions: {image_info['width']}x{image_info['height']}")
                self.logger.info(f"   Format: {image_info['format']}")
            
            # Provide feedback to user on Frame display
            await self.interface.display_text(f"Photo {self.photo_count} saved!")
            await asyncio.sleep(1.5)  # Show message briefly
            await self.interface.display_text("Tap for photo")
            
        except Exception as e:
            self.logger.error(f"Failed to save photo: {e}")
            await self.interface.display_text("Save failed!")
    
    async def on_tap_detected(self):
        """
        Handle tap detection events with immediate feedback.
        
        This provides immediate visual confirmation that the tap was detected,
        before photo capture processing begins.
        """
        self.logger.info("👆 Tap detected - triggering photo capture")
        
        # Immediate feedback to user
        await self.interface.display_text("Capturing...")
        
        # You could add additional logic here, such as:
        # - Playing a sound
        # - Logging user interaction patterns
        # - Adjusting capture settings based on context
    
    async def on_error(self, error: Exception):
        """
        Handle errors with logging and user notification.
        
        Args:
            error: The exception that occurred
        """
        self.logger.error(f"❌ Frame error: {error}")
        
        # Try to display error on Frame (if still connected)
        try:
            await self.interface.display_text("Error occurred")
        except:
            pass  # Frame might be disconnected
    
    async def on_status_update(self, status: dict):
        """
        Handle periodic status updates for monitoring.
        
        Args:
            status: Device status dictionary
        """
        if status["connected"]:
            battery = status.get("battery_level", "Unknown")
            memory = status.get("memory_usage", "Unknown")
            captures = status.get("capture_count", 0)
            
            self.logger.info(f"📊 Status - Battery: {battery}%, Memory: {memory}KB, Photos: {captures}")
            
            # Warn if battery is low
            if isinstance(battery, int) and battery < 20:
                await self.interface.display_text("Low battery!")
                await asyncio.sleep(2)
                await self.interface.display_text("Tap for photo")
    
    async def setup_callbacks(self):
        """Configure all event callbacks for the Frame interface."""
        self.interface.set_photo_callback(self.on_photo_captured)
        self.interface.set_tap_callback(self.on_tap_detected)
        self.interface.set_error_callback(self.on_error)
        self.interface.set_status_callback(self.on_status_update)
    
    async def connect_with_retries(self, max_retries: int = 5):
        """
        Connect to Frame glasses with comprehensive retry logic.
        
        Args:
            max_retries: Maximum number of connection attempts
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.logger.info("🔗 Connecting to Frame glasses...")
        
        for attempt in range(max_retries):
            result = await self.interface.connect(max_retries=1)
            
            if result["success"]:
                self.logger.info("✅ Connected successfully!")
                self.logger.info(f"   Battery: {result.get('battery_level', 'Unknown')}%")
                self.logger.info(f"   Memory: {result.get('memory_usage', 'Unknown')}KB")
                return True
            else:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {result['error']}")
                
                if attempt < max_retries - 1:
                    wait_time = min(5 * (attempt + 1), 30)  # Exponential backoff, max 30s
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        self.logger.error("❌ Failed to connect after all retries")
        return False
    
    async def run(self):
        """
        Main application loop with complete lifecycle management.
        
        This method handles:
        - Connection establishment
        - Event loop execution
        - Graceful shutdown
        - Error recovery
        """
        try:
            # Setup event callbacks
            await self.setup_callbacks()
            
            # Connect to Frame glasses
            if not await self.connect_with_retries():
                return
            
            # Display welcome message
            await self.interface.display_text("Photo app ready!")
            await asyncio.sleep(2)
            await self.interface.display_text("Tap for photo")
            
            # Get initial status
            status = await self.interface.get_status()
            await self.on_status_update(status)
            
            self.logger.info("🎯 App running - tap Frame glasses to capture photos")
            self.logger.info("   Press Ctrl+C to stop")
            
            # Run main event loop
            await self.interface.run_event_loop(status_update_interval=30.0)
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Shutdown requested by user")
        except Exception as e:
            self.logger.error(f"💥 Unexpected error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Perform clean shutdown of the application."""
        self.logger.info("🔄 Shutting down Frame photo app...")
        
        try:
            # Display goodbye message
            if self.interface.is_connected:
                await self.interface.display_text("Goodbye!")
                await asyncio.sleep(1)
            
            # Stop the interface
            await self.interface.stop()
            
            # Final statistics
            self.logger.info(f"📈 Session complete: {self.photo_count} photos captured")
            self.logger.info(f"   Photos saved to: {self.save_directory.absolute()}")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.logger.info("✅ Shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """
    Main entry point with comprehensive error handling.
    
    This function provides the top-level application structure
    and ensures proper cleanup even in error scenarios.
    """
    app = FramePhotoApp()
    
    try:
        # Setup signal handlers for clean shutdown
        app.setup_signal_handlers()
        
        # Run the main application
        await app.run()
        
    except Exception as e:
        app.logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🔮 Frame Photo Capture App")
    print("=" * 30)
    print("Make sure your Frame glasses are:")
    print("- Charged and powered on")
    print("- Paired with this device via Bluetooth")
    print("- Within range (close to computer)")
    print()
    
    # Check system requirements
    try:
        import frame_msg
        import frame_ble
        print("✅ Frame SDK packages found")
    except ImportError as e:
        print(f"❌ Missing Frame SDK packages: {e}")
        print("Install with: pip install frame-msg frame-ble")
        sys.exit(1)
    
    # Run the application
    asyncio.run(main()) 