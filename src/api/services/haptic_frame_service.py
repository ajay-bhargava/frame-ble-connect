import asyncio
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.api.services.parking_service import ParkingService
from src.api.services.frame_service import FrameService

class HapticFrameService(FrameService):
    """Enhanced Frame service with haptic-triggered capture and violation checking"""
    
    def __init__(self):
        super().__init__()
        self.parking_service = ParkingService()
        self.haptic_monitoring_active = False
        self.haptic_callback = None
        self.monitoring_task = None
        
    async def connect(self, haptic_mode: bool = False) -> Dict[str, Any]:
        """
        Connect to Frame glasses with optional haptic mode
        
        Args:
            haptic_mode: Whether to enable haptic monitoring
            
        Returns:
            Connection result
        """
        try:
            # Connect using parent class method
            result = await super().connect()
            
            if result.get("success") and haptic_mode:
                # Initialize haptic mode
                self.haptic_monitoring_active = False
                result["haptic_mode"] = True
                result["message"] = "Connected to Frame glasses in haptic mode"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect in haptic mode: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_haptic_monitoring(self, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Start monitoring for haptic-triggered captures
        
        Args:
            callback: Optional callback function for capture events
            
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
            
            self.haptic_callback = callback
            self.haptic_monitoring_active = True
            
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitor_haptic_events())
            
            return {
                "success": True,
                "message": "Haptic monitoring started",
                "monitoring_active": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start haptic monitoring: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_haptic_monitoring(self) -> Dict[str, Any]:
        """
        Stop haptic monitoring
        
        Returns:
            Monitoring stop result
        """
        try:
            self.haptic_monitoring_active = False
            
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                self.monitoring_task = None
            
            return {
                "success": True,
                "message": "Haptic monitoring stopped",
                "monitoring_active": False,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop haptic monitoring: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _monitor_haptic_events(self):
        """
        Monitor for haptic-triggered capture events
        This would integrate with the Lua app's touch detection
        """
        while self.haptic_monitoring_active:
            try:
                # Check for haptic events (this would be implemented based on the Lua app)
                # For now, we'll simulate the monitoring
                await asyncio.sleep(0.1)  # Poll every 100ms
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in haptic monitoring: {e}")
                await asyncio.sleep(1)
    
    async def process_haptic_capture(self, image_data: bytes, trigger_type: str = "touch") -> Dict[str, Any]:
        """
        Process a haptic-triggered capture with violation checking
        
        Args:
            image_data: Captured image data
            trigger_type: Type of trigger (touch, voice, etc.)
            
        Returns:
            Processing result with violation analysis
        """
        try:
            # Step 1: Capture the image
            capture_result = await self.capture_image(720)  # 720p resolution
            
            if not capture_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to capture image",
                    "trigger_type": trigger_type,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Analyze the image for parking signs
            analysis_result = await self._analyze_parking_sign(image_data)
            
            if not analysis_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to analyze parking sign",
                    "trigger_type": trigger_type,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 3: Check violations if zone number found
            zone_number = analysis_result.get("zone_number")
            violation_result = None
            feedback_message = None
            
            if zone_number:
                violation_result = await self._check_violations(zone_number)
                feedback_message = self._generate_feedback_message(violation_result)
                
                # Send feedback to glasses
                if feedback_message:
                    await self.display_text(feedback_message)
            
            # Step 4: Call callback if provided
            if self.haptic_callback:
                callback_data = {
                    "success": True,
                    "trigger_type": trigger_type,
                    "image_size_bytes": capture_result.get("image_size_bytes"),
                    "resolution": capture_result.get("resolution"),
                    "timestamp": datetime.now().isoformat(),
                    "analysis": analysis_result,
                    "violation_check": violation_result,
                    "feedback_message": feedback_message
                }
                
                # Call callback asynchronously
                asyncio.create_task(self._call_callback(callback_data))
            
            return {
                "success": True,
                "trigger_type": trigger_type,
                "image_size_bytes": capture_result.get("image_size_bytes"),
                "resolution": capture_result.get("resolution"),
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis_result,
                "violation_check": violation_result,
                "feedback_message": feedback_message
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process haptic capture: {str(e)}",
                "trigger_type": trigger_type,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_parking_sign(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze captured image for parking sign information
        
        Args:
            image_data: Captured image data
            
        Returns:
            Analysis result with zone number and other details
        """
        try:
            # This would integrate with your vision LLM for OCR and analysis
            # For now, we'll use a placeholder that could be enhanced
            
            # Convert image to base64 for API calls
            import base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Here you would call your vision LLM API
            # For now, we'll simulate finding a zone number
            # In production, this would be:
            # - Send image to vision LLM
            # - Extract OCR text
            # - Parse for zone numbers
            
            # Simulated analysis result
            analysis_result = {
                "success": True,
                "zone_number": "106185",  # This would come from vision LLM
                "ocr_text": "PAY BY CELL 106185",  # This would come from vision LLM
                "confidence": 0.95,
                "timestamp": datetime.now().isoformat()
            }
            
            return analysis_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze parking sign: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_violations(self, zone_number: str) -> Dict[str, Any]:
        """
        Check violation count for a zone number
        
        Args:
            zone_number: The pay-by-cell zone number
            
        Returns:
            Violation check result
        """
        try:
            violation_result = await self.parking_service.get_violation_count_by_zone(zone_number)
            
            if violation_result.get("success"):
                violation_count = violation_result.get("violation_count", 0)
                
                return {
                    "success": True,
                    "zone_number": zone_number,
                    "violation_count": violation_count,
                    "street_name": violation_result.get("street_name"),
                    "threshold_exceeded": violation_count > 20,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": violation_result.get("error"),
                    "zone_number": zone_number,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check violations: {str(e)}",
                "zone_number": zone_number,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_feedback_message(self, violation_result: Dict[str, Any]) -> Optional[str]:
        """
        Generate feedback message based on violation count
        
        Args:
            violation_result: Result from violation check
            
        Returns:
            Feedback message to display on glasses
        """
        if not violation_result.get("success"):
            return "Error checking violations"
        
        violation_count = violation_result.get("violation_count", 0)
        
        if violation_count > 20:
            return "Foggetaboutit"
        else:
            return "Don't worry about it"
    
    async def _call_callback(self, data: Dict[str, Any]):
        """
        Call the haptic callback function
        
        Args:
            data: Data to pass to callback
        """
        try:
            if self.haptic_callback and callable(self.haptic_callback):
                if asyncio.iscoroutinefunction(self.haptic_callback):
                    await self.haptic_callback(data)
                else:
                    self.haptic_callback(data)
        except Exception as e:
            print(f"Error in haptic callback: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current haptic service status
        
        Returns:
            Status information
        """
        try:
            base_status = await super().get_status()
            
            return {
                **base_status,
                "haptic_mode": True,
                "monitoring_active": self.haptic_monitoring_active,
                "parking_service_available": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "connected": False,
                "haptic_mode": False,
                "monitoring_active": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect and cleanup haptic monitoring
        
        Returns:
            Disconnect result
        """
        try:
            # Stop haptic monitoring
            await self.stop_haptic_monitoring()
            
            # Close parking service
            await self.parking_service.close()
            
            # Disconnect using parent method
            return await super().disconnect()
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to disconnect: {str(e)}",
                "timestamp": datetime.now().isoformat()
            } 