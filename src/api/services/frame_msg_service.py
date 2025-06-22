import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add the connect module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'connect'))
from frame_msg import FrameMsg, RxPhoto, TxCaptureSettings

class FrameService:
    """Service for managing Frame glasses connection and operations"""
    
    def __init__(self):
        self.frame: Optional[FrameMsg] = None
        self.rx_photo: Optional[RxPhoto] = None
        self.photo_queue: Optional[asyncio.Queue] = None
        self.is_connected = False
        self.last_capture_time: Optional[datetime] = None
        
    async def connect(self) -> Dict[str, Any]:
        """Connect to Frame glasses"""
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
            
            # Upload camera app
            lua_file_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'connect', 'lua', 'camera_frame_app.lua'
            )
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
                "message": "Connected to Frame glasses"
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
            if self.rx_photo and self.frame:
                self.rx_photo.detach(self.frame)
            if self.frame:
                self.frame.detach_print_response_handler()
                await self.frame.stop_frame_app()
                await self.frame.disconnect()
            
            self.is_connected = False
            self.frame = None
            self.rx_photo = None
            self.photo_queue = None
            
        except Exception as e:
            print(f"Error disconnecting: {e}")
    
    async def capture_image(self, resolution: int = 720) -> Dict[str, Any]:
        """Capture an image from the Frame glasses"""
        if not self.is_connected or not self.frame:
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
                "timestamp": self.last_capture_time.isoformat()
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
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current device status"""
        if not self.is_connected or not self.frame:
            return {
                "connected": False,
                "battery_level": None,
                "memory_usage": None,
                "last_capture": None
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
                "last_capture": self.last_capture_time.isoformat() if self.last_capture_time else None
            }
            
        except Exception as e:
            return {
                "connected": True,
                "battery_level": None,
                "memory_usage": None,
                "last_capture": self.last_capture_time.isoformat() if self.last_capture_time else None,
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