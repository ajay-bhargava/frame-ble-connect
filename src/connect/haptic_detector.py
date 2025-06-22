import asyncio
import time
import math
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Import Frame glasses libraries
from frame_ble import FrameBle
from frame_msg import FrameMsg, RxPhoto, TxCaptureSettings

class HapticDetector:
    """
    Light tap detection service for Frame glasses using real accelerometer data
    """
    
    def __init__(self):
        self.is_connected = False
        self.is_monitoring = False
        self.touch_callback = None
        self.monitoring_task = None
        
        # Light tap detection parameters
        self.accel_threshold = 1.5  # Lower threshold for light tap
        self.gyro_threshold = 0.8   # Filter out head movements
        self.touch_cooldown = 0.5   # Seconds between touches
        self.last_touch_time = 0
        
        # Accelerometer data storage
        self.last_accel = {'x': 0, 'y': 0, 'z': 0}
        self.last_gyro = {'x': 0, 'y': 0, 'z': 0}
        
        # Frame glasses connection
        self.frame = None
        self.rx_photo = None
        self.photo_queue = None
        
    async def connect_to_glasses(self) -> Dict[str, Any]:
        """
        Connect to Frame glasses via BLE
        
        Returns:
            Connection result
        """
        try:
            print("🔗 Connecting to Frame glasses...")
            
            # Initialize Frame connection
            self.frame = FrameMsg()
            await self.frame.connect()
            
            # Check battery and memory
            batt_mem = await self.frame.send_lua(
                'print(frame.battery_level() .. " / " .. collectgarbage("count"))', 
                await_print=True
            )
            print(f"Battery Level/Memory used: {batt_mem}")
            
            # Upload required libraries
            await self.frame.upload_stdlua_libs(lib_names=['data', 'camera'])
            
            # Upload haptic camera app
            import os
            lua_file_path = os.path.join(os.path.dirname(__file__), "lua", "haptic_camera_app.lua")
            await self.frame.upload_frame_app(local_filename=lua_file_path)
            
            # Attach print response handler
            self.frame.attach_print_response_handler()
            
            # Start the frame app
            await self.frame.start_frame_app()
            
            # Set up photo receiver
            self.rx_photo = RxPhoto()
            self.photo_queue = await self.rx_photo.attach(self.frame)
            
            # Let autoexposure settle
            print("Letting autoexposure settle...")
            await asyncio.sleep(2.0)
            
            self.is_connected = True
            
            return {
                "success": True,
                "message": "Connected to Frame glasses",
                "battery_memory": batt_mem,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_touch_monitoring(self, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Start monitoring for light tap events using real accelerometer data
        
        Args:
            callback: Function to call when touch is detected
            
        Returns:
            Monitoring start result
        """
        try:
            if not self.is_connected:
                return {
                    "success": False,
                    "error": "Not connected to Frame glasses",
                    "timestamp": datetime.now().isoformat()
                }
            
            self.touch_callback = callback
            self.is_monitoring = True
            
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitor_accelerometer())
            
            return {
                "success": True,
                "message": "Light tap monitoring started - tap temple area to capture",
                "monitoring_active": True,
                "sensitivity": "light_tap",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start monitoring: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_touch_monitoring(self) -> Dict[str, Any]:
        """
        Stop touch monitoring
        
        Returns:
            Monitoring stop result
        """
        try:
            self.is_monitoring = False
            
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                self.monitoring_task = None
            
            return {
                "success": True,
                "message": "Touch monitoring stopped",
                "monitoring_active": False,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop monitoring: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _monitor_accelerometer(self):
        """
        Monitor real accelerometer data for light tap detection
        """
        print("👁️  Monitoring accelerometer for light taps...")
        print("   Tap the temple area (side of glasses) to trigger capture")
        
        while self.is_monitoring:
            try:
                # Get real accelerometer and gyroscope data from Frame glasses
                accel_data = await self._get_real_accelerometer_data()
                gyro_data = await self._get_real_gyroscope_data()
                
                if accel_data and gyro_data:
                    # Check for light tap
                    if self._detect_light_tap(accel_data, gyro_data):
                        await self._handle_touch_detected()
                
                # Poll at 50Hz for responsive detection (slower than simulated to avoid overwhelming the glasses)
                await asyncio.sleep(0.02)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in accelerometer monitoring: {e}")
                await asyncio.sleep(0.1)
    
    async def _get_real_accelerometer_data(self) -> Optional[Dict[str, float]]:
        """
        Get real accelerometer data from Frame glasses
        
        Returns:
            Accelerometer data or None if not available
        """
        try:
            # Get accelerometer data from Frame glasses
            accel_result = await self.frame.send_lua(
                'local accel = frame.imu.accelerometer(); if accel then print(accel.x .. "," .. accel.y .. "," .. accel.z) else print("none") end',
                await_print=True
            )
            
            if accel_result and accel_result != "none":
                # Parse the accelerometer data
                try:
                    x, y, z = map(float, accel_result.split(','))
                    return {
                        'x': x,
                        'y': y,
                        'z': z,
                        'timestamp': time.time()
                    }
                except ValueError:
                    return None
            
            return None
            
        except Exception as e:
            print(f"Error reading accelerometer: {e}")
            return None
    
    async def _get_real_gyroscope_data(self) -> Optional[Dict[str, float]]:
        """
        Get real gyroscope data from Frame glasses
        
        Returns:
            Gyroscope data or None if not available
        """
        try:
            # Get gyroscope data from Frame glasses
            gyro_result = await self.frame.send_lua(
                'local gyro = frame.imu.gyroscope(); if gyro then print(gyro.x .. "," .. gyro.y .. "," .. gyro.z) else print("none") end',
                await_print=True
            )
            
            if gyro_result and gyro_result != "none":
                # Parse the gyroscope data
                try:
                    x, y, z = map(float, gyro_result.split(','))
                    return {
                        'x': x,
                        'y': y,
                        'z': z,
                        'timestamp': time.time()
                    }
                except ValueError:
                    return None
            
            return None
            
        except Exception as e:
            print(f"Error reading gyroscope: {e}")
            return None
    
    def _detect_light_tap(self, accel_data: Dict[str, float], gyro_data: Dict[str, float]) -> bool:
        """
        Detect light tap using real accelerometer and gyroscope data
        
        Args:
            accel_data: Current accelerometer readings
            gyro_data: Current gyroscope readings
            
        Returns:
            True if light tap detected, False otherwise
        """
        try:
            current_time = time.time()
            
            # Check cooldown period
            if current_time - self.last_touch_time < self.touch_cooldown:
                return False
            
            # Calculate acceleration change
            accel_change_x = abs(accel_data['x'] - self.last_accel['x'])
            accel_change_y = abs(accel_data['y'] - self.last_accel['y'])
            accel_change_z = abs(accel_data['z'] - self.last_accel['z'])
            
            total_accel_change = accel_change_x + accel_change_y + accel_change_z
            
            # Calculate gyroscope magnitude (to filter out head movements)
            gyro_magnitude = math.sqrt(
                gyro_data['x']**2 + gyro_data['y']**2 + gyro_data['z']**2
            )
            
            # Light tap detection criteria:
            # 1. Acceleration change above threshold (but not too high for light tap)
            # 2. Gyroscope magnitude below threshold (not a head movement)
            # 3. Within reasonable bounds for a light tap
            
            is_light_tap = (
                total_accel_change > self.accel_threshold and
                total_accel_change < 5.0 and  # Upper bound for light tap
                gyro_magnitude < self.gyro_threshold
            )
            
            # Update last readings
            self.last_accel = accel_data.copy()
            self.last_gyro = gyro_data.copy()
            
            if is_light_tap:
                self.last_touch_time = current_time
                print(f"👆 Light tap detected! Accel change: {total_accel_change:.2f}, Gyro: {gyro_magnitude:.2f}")
            
            return is_light_tap
            
        except Exception as e:
            print(f"Error in light tap detection: {e}")
            return False
    
    async def _handle_touch_detected(self):
        """
        Handle detected light tap event - capture photo and get violation count
        """
        try:
            print("🎯 Light tap detected! Triggering photo capture...")
            
            # Trigger photo capture
            capture_result = await self._capture_photo()
            
            # Get violation count (simplified for now)
            violation_count = await self._get_violation_count()
            
            # Call callback if provided
            if self.touch_callback:
                callback_data = {
                    "success": True,
                    "trigger_type": "light_tap",
                    "timestamp": datetime.now().isoformat(),
                    "capture_result": capture_result,
                    "violation_count": violation_count
                }
                
                if asyncio.iscoroutinefunction(self.touch_callback):
                    await self.touch_callback(callback_data)
                else:
                    self.touch_callback(callback_data)
            
            print(f"✅ Photo captured! Violation count: {violation_count}")
            
        except Exception as e:
            print(f"Error handling touch: {e}")
    
    async def _capture_photo(self) -> Dict[str, Any]:
        """
        Capture photo from Frame glasses
        
        Returns:
            Capture result
        """
        try:
            # Request photo capture
            await self.frame.send_message(0x0d, TxCaptureSettings(resolution=720).pack())
            
            # Wait for photo data
            jpeg_bytes = await asyncio.wait_for(self.photo_queue.get(), timeout=10.0)
            
            return {
                "success": True,
                "image_size_bytes": len(jpeg_bytes),
                "resolution": "720p",
                "jpeg_data": jpeg_bytes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_violation_count(self) -> int:
        """
        Get violation count for testing
        
        Returns:
            Simulated violation count (will be replaced with real violation checking)
        """
        try:
            # TODO: Integrate with actual violation checking service
            # For now, return simulated count
            
            import random
            return random.randint(5, 35)  # Random count for testing
            
        except Exception as e:
            print(f"Error getting violation count: {e}")
            return 0
    
    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from Frame glasses
        
        Returns:
            Disconnect result
        """
        try:
            await self.stop_touch_monitoring()
            
            # Clean up Frame connection
            if self.rx_photo and self.frame:
                self.rx_photo.detach(self.frame)
            
            if self.frame:
                self.frame.detach_print_response_handler()
                await self.frame.stop_frame_app()
                await self.frame.disconnect()
            
            self.is_connected = False
            
            return {
                "success": True,
                "message": "Disconnected from Frame glasses",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to disconnect: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current detector status
        
        Returns:
            Status information
        """
        return {
            "connected": self.is_connected,
            "monitoring_active": self.is_monitoring,
            "sensitivity": "light_tap",
            "accel_threshold": self.accel_threshold,
            "gyro_threshold": self.gyro_threshold,
            "touch_cooldown": self.touch_cooldown,
            "timestamp": datetime.now().isoformat()
        } 