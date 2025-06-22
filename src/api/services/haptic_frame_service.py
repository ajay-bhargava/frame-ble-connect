# pylint: disable=import-error
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.api.services.parking_service import ParkingService  # pylint: disable=import-error
from src.api.services.frame_service import FrameService  # pylint: disable=import-error
from src.connect.haptic_detector import HapticDetector  # pylint: disable=import-error

class HapticFrameService(FrameService):
    """Enhanced Frame service with haptic-triggered capture and violation checking"""
    
    def __init__(self):
        super().__init__()
        self.parking_service = ParkingService()
        self.haptic_detector = HapticDetector()
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
            if haptic_mode:
                # Use the real haptic detector for haptic mode
                result = await self.haptic_detector.connect_to_glasses()
                
                if result.get("success"):
                    self.haptic_monitoring_active = False
                    result["haptic_mode"] = True
                    result["message"] = "Connected to Frame glasses in haptic mode"
                
                return result
            else:
                # Use parent class method for regular mode
                result = await super().connect()
                return result
            
        except (RuntimeError, ValueError, OSError) as e:
            return {
                "success": False,
                "error": f"Failed to connect in haptic mode: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_haptic_monitoring(self, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Start monitoring for haptic-triggered captures using real accelerometer data
        
        Args:
            callback: Optional callback function for capture events
            
        Returns:
            Monitoring start result
        """
        try:
            if not self.haptic_detector.is_connected:
                return {
                    "success": False,
                    "error": "Not connected to Frame glasses",
                    "timestamp": datetime.now().isoformat()
                }
            
            self.haptic_callback = callback
            self.haptic_monitoring_active = True
            
            # Start monitoring using the real haptic detector
            result = await self.haptic_detector.start_touch_monitoring(self._haptic_callback_wrapper)
            
            if result.get("success"):
                self.monitoring_task = self.haptic_detector.monitoring_task
            
            return result
            
        except (RuntimeError, ValueError, OSError) as e:
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
            
            if self.haptic_detector:
                result = await self.haptic_detector.stop_touch_monitoring()
                self.monitoring_task = None
                return result
            
            return {
                "success": True,
                "message": "Haptic monitoring stopped",
                "monitoring_active": False,
                "timestamp": datetime.now().isoformat()
            }
            
        except (RuntimeError, ValueError, OSError) as e:
            return {
                "success": False,
                "error": f"Failed to stop haptic monitoring: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _haptic_callback_wrapper(self, data: Dict[str, Any]):
        """
        Wrapper for haptic detector callback to integrate with violation checking
        
        Args:
            data: Data from haptic detector
        """
        try:
            # Extract capture result
            capture_result = data.get("capture_result", {})
            
            if capture_result.get("success"):
                # Get the captured image data
                jpeg_data = capture_result.get("jpeg_data")
                
                if jpeg_data:
                    # Analyze the image for parking signs
                    analysis_result = await self._analyze_parking_sign(jpeg_data)
                    
                    # Check violations if zone number found
                    zone_number = analysis_result.get("zone_number")
                    violation_result = None
                    feedback_message = None
                    
                    if zone_number:
                        violation_result = await self._check_violations(zone_number)
                        feedback_message = self._generate_feedback_message(violation_result)
                        
                        # Send feedback to glasses
                        if feedback_message and self.haptic_detector and self.haptic_detector.frame:
                            await self.haptic_detector.frame.send_lua(
                                f'frame.display.text("{feedback_message}", 1, 1); frame.display.show()',
                                await_print=True
                            )
                    
                    # Update the data with analysis results
                    data["analysis"] = analysis_result
                    data["violation_check"] = violation_result
                    data["feedback_message"] = feedback_message
            
            # Call the original callback if provided
            if self.haptic_callback:
                if asyncio.iscoroutinefunction(self.haptic_callback):
                    await self.haptic_callback(data)
                else:
                    self.haptic_callback(data)
                    
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error in haptic callback wrapper: {e}")
    
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
            # image_b64 = base64.b64encode(image_data).decode('utf-8')  # Unused variable removed
            
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
            
        except (RuntimeError, ValueError, OSError) as e:
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
                
        except (RuntimeError, ValueError, OSError) as e:
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
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current haptic service status
        
        Returns:
            Status information
        """
        try:
            if self.haptic_detector and self.haptic_detector.is_connected:
                base_status = self.haptic_detector.get_status()
                
                return {
                    **base_status,
                    "haptic_mode": True,
                    "parking_service_available": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "connected": False,
                    "haptic_mode": False,
                    "monitoring_active": False,
                    "error": "Not connected to Frame glasses",
                    "timestamp": datetime.now().isoformat()
                }
            
        except (RuntimeError, ValueError, OSError) as e:
            return {
                "connected": False,
                "haptic_mode": False,
                "monitoring_active": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def disconnect(self) -> None:
        """
        Disconnect and cleanup haptic monitoring
        
        Returns:
            None
        """
        try:
            # Stop haptic monitoring
            await self.stop_haptic_monitoring()
            
            # Close parking service
            await self.parking_service.close()
            
            # Disconnect haptic detector
            if self.haptic_detector:
                await self.haptic_detector.disconnect()
            else:
                # Fallback to parent disconnect
                await super().disconnect()
            
        except (RuntimeError, ValueError, OSError) as e:
            print(f"Error during disconnect: {e}")
            # Ensure we still try to disconnect parent
            try:
                await super().disconnect()
            except Exception as e2:  # pylint: disable=broad-except
                print(f"Error during fallback disconnect: {e2}") 