import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import sys
import os

# Add the connect module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'connect'))
from frame_msg import FrameMsg, RxPhoto, TxCaptureSettings

class HapticFrameService:
    """Enhanced Frame service with haptic-triggered photo capture capabilities"""
    
    def __init__(self):
        self.frame: Optional[FrameMsg] = None
        self.rx_photo: Optional[RxPhoto] = None
        self.photo_queue: Optional[asyncio.Queue] = None
        self.is_connected = False
        self.last_capture_time: Optional[datetime] = None
        self.is_haptic_mode = False
        self.haptic_callback: Optional[Callable] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
    async def connect(self, haptic_mode: bool = False) -> Dict[str, Any]:
        """Connect to Frame glasses with optional haptic mode"""
        try:
            self.frame = FrameMsg()
            await self.frame.connect()
            
            # Check battery and memory
            batt_mem = await self.frame.send_lua(
                'print(frame.battery_level() .. " / " .. collectgarbage("count"))', 
                await_print=True
            )
            
            # Upload required Lua libraries
            await self.frame.upload_stdlua_libs(lib_names=['data', 'camera'])
            
            # Choose the appropriate Lua app based on mode
            if haptic_mode:
                lua_file_path = os.path.join(
                    os.path.dirname(__file__), 
                    '..', '..', 'connect', 'lua', 'haptic_camera_app.lua'
                )
                self.is_haptic_mode = True
            else:
                lua_file_path = os.path.join(
                    os.path.dirname(__file__), 
                    '..', '..', 'connect', 'lua', 'camera_frame_app.lua'
                )
            
            # Upload the selected app
            await self.frame.upload_frame_app(local_filename=lua_file_path)
            
            # Start the frame app
            await self.frame.start_frame_app()
            
            # Set up photo receiver
            self.rx_photo = RxPhoto()
            self.photo_queue = await self.rx_photo.attach(self.frame)
            
            self.is_connected = True
            
            return {
                "success": True,
                "battery_memory": batt_mem,
                "message": f"Connected to Frame glasses in {'haptic' if haptic_mode else 'manual'} mode",
                "haptic_mode": haptic_mode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to connect to Frame glasses"
            }
    
    async def disconnect(self):
        """Disconnect from Frame glasses"""
        try:
            # Stop haptic monitoring if running
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            if self.rx_photo and self.frame:
                self.rx_photo.detach(self.frame)
            if self.frame:
                self.frame.detach_print_response_handler()
                await self.frame.stop_frame_app()
                await self.frame.disconnect()
            
            self.is_connected = False
            self.is_haptic_mode = False
            self.frame = None
            self.rx_photo = None
            self.photo_queue = None
            self.haptic_callback = None
            
        except Exception as e:
            print(f"Error disconnecting: {e}")
    
    async def capture_image(self, resolution: int = 720) -> Dict[str, Any]:
        """Capture an image from the Frame glasses"""
        if not self.is_connected or not self.frame or not self.photo_queue:
            return {
                "success": False,
                "error": "Not connected to Frame glasses"
            }
        
        try:
            # Request photo capture
            await self.frame.send_message(0x0d, TxCaptureSettings(resolution=resolution).pack())
            
            # Wait for photo data
            jpeg_bytes = await asyncio.wait_for(self.photo_queue.get(), timeout=10.0)
            
            self.last_capture_time = datetime.now()
            
            return {
                "success": True,
                "image_data": jpeg_bytes,
                "image_size_bytes": len(jpeg_bytes),
                "resolution": resolution,
                "timestamp": self.last_capture_time.isoformat(),
                "trigger_type": "manual"
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout waiting for image capture"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def start_haptic_monitoring(self, callback: Callable[[Dict[str, Any]], None]):
        """Start monitoring for haptic-triggered photo captures"""
        if not self.is_haptic_mode:
            return {
                "success": False,
                "error": "Not in haptic mode"
            }
        
        if self.monitoring_task and not self.monitoring_task.done():
            return {
                "success": False,
                "error": "Haptic monitoring already running"
            }
        
        self.haptic_callback = callback
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitor_haptic_captures())
        
        return {
            "success": True,
            "message": "Haptic monitoring started"
        }
    
    async def stop_haptic_monitoring(self):
        """Stop haptic monitoring"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.haptic_callback = None
        
        return {
            "success": True,
            "message": "Haptic monitoring stopped"
        }
    
    async def _monitor_haptic_captures(self):
        """Internal method to monitor for haptic-triggered captures"""
        try:
            while self.is_connected and self.is_haptic_mode and self.photo_queue:
                try:
                    # Wait for photo data with a shorter timeout for responsiveness
                    jpeg_bytes = await asyncio.wait_for(self.photo_queue.get(), timeout=1.0)
                    
                    # Process the haptic-triggered capture
                    capture_result = {
                        "success": True,
                        "image_data": jpeg_bytes,
                        "image_size_bytes": len(jpeg_bytes),
                        "resolution": 720,  # Default for haptic captures
                        "timestamp": datetime.now().isoformat(),
                        "trigger_type": "haptic"
                    }
                    
                    self.last_capture_time = datetime.now()
                    
                    # Call the callback with the capture result
                    if self.haptic_callback:
                        try:
                            await self.haptic_callback(capture_result)
                        except Exception as e:
                            print(f"Error in haptic callback: {e}")
                    
                except asyncio.TimeoutError:
                    # No photo received, continue monitoring
                    continue
                except Exception as e:
                    print(f"Error in haptic monitoring: {e}")
                    await asyncio.sleep(0.1)
                    
        except asyncio.CancelledError:
            print("Haptic monitoring cancelled")
        except Exception as e:
            print(f"Haptic monitoring error: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current device status"""
        if not self.is_connected or not self.frame:
            return {
                "connected": False,
                "battery_level": None,
                "memory_usage": None,
                "last_capture": None,
                "haptic_mode": False,
                "monitoring_active": False
            }
        
        try:
            # Get battery and memory info
            batt_mem = await self.frame.send_lua(
                'print(frame.battery_level() .. " / " .. collectgarbage("count"))', 
                await_print=True
            )
            
            battery_level = None
            memory_usage = None
            
            if batt_mem:
                try:
                    parts = batt_mem.split(' / ')
                    if len(parts) == 2:
                        battery_level = int(parts[0])
                        memory_usage = parts[1]
                except:
                    pass
            
            return {
                "connected": True,
                "battery_level": battery_level,
                "memory_usage": memory_usage,
                "last_capture": self.last_capture_time.isoformat() if self.last_capture_time else None,
                "haptic_mode": self.is_haptic_mode,
                "monitoring_active": self.monitoring_task is not None and not self.monitoring_task.done()
            }
            
        except Exception as e:
            return {
                "connected": True,
                "battery_level": None,
                "memory_usage": None,
                "last_capture": self.last_capture_time.isoformat() if self.last_capture_time else None,
                "haptic_mode": self.is_haptic_mode,
                "monitoring_active": self.monitoring_task is not None and not self.monitoring_task.done(),
                "error": str(e)
            }
    
    async def display_text(self, text: str) -> Dict[str, Any]:
        """Display text on the Frame glasses"""
        if not self.is_connected or not self.frame:
            return {
                "success": False,
                "error": "Not connected to Frame glasses"
            }
        
        try:
            # Truncate text if too long for display
            display_text = text[:50] if len(text) > 50 else text
            
            await self.frame.print_short_text(display_text)
            
            return {
                "success": True,
                "message": f"Displayed: {display_text}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 