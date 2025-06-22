from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
import asyncio
import time

from src.api.models.requests import CaptureRequest
from src.api.models.responses import DeviceStatus, CaptureResult

router = APIRouter(prefix="/haptic", tags=["haptic"])

# Global haptic service instance
_haptic_service = None
_haptic_callback_task = None

async def haptic_capture_callback(capture_result: Dict[str, Any]):
    """Callback function for haptic-triggered captures"""
    print(f"🎯 Haptic capture triggered: {capture_result['timestamp']}")
    print(f"   Image size: {capture_result['image_size_bytes']} bytes")
    print(f"   Trigger type: {capture_result['trigger_type']}")
    
    # Here you can add additional processing like:
    # - Save the image
    # - Send to AI analysis
    # - Display feedback on glasses
    # - Send to external services
    
    # For now, just display a confirmation on the glasses
    if _haptic_service:
        await _haptic_service.display_text("Photo taken!")

@router.post("/connect")
async def connect_haptic_mode():
    """
    Connect to Frame glasses in haptic mode for touch-triggered photo capture
    """
    global _haptic_service
    
    try:
        from src.api.services.haptic_frame_service import HapticFrameService
        
        _haptic_service = HapticFrameService()
        result = await _haptic_service.connect(haptic_mode=True)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "message": result["message"],
            "battery_memory": result.get("battery_memory"),
            "haptic_mode": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect in haptic mode: {str(e)}")

@router.post("/disconnect")
async def disconnect_haptic_mode():
    """
    Disconnect from Frame glasses and stop haptic monitoring
    """
    global _haptic_service, _haptic_callback_task
    
    try:
        if _haptic_service:
            # Stop haptic monitoring
            await _haptic_service.stop_haptic_monitoring()
            
            # Disconnect
            await _haptic_service.disconnect()
            _haptic_service = None
        
        if _haptic_callback_task and not _haptic_callback_task.done():
            _haptic_callback_task.cancel()
            _haptic_callback_task = None
        
        return {
            "success": True,
            "message": "Disconnected from Frame glasses and stopped haptic monitoring"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

@router.post("/start-monitoring")
async def start_haptic_monitoring():
    """
    Start monitoring for haptic-triggered photo captures
    """
    global _haptic_service, _haptic_callback_task
    
    try:
        if not _haptic_service:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        result = await _haptic_service.start_haptic_monitoring(haptic_capture_callback)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "message": "Haptic monitoring started - touch the glasses to capture photos!",
            "status": "monitoring_active"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start haptic monitoring: {str(e)}")

@router.post("/stop-monitoring")
async def stop_haptic_monitoring():
    """
    Stop monitoring for haptic-triggered photo captures
    """
    global _haptic_service, _haptic_callback_task
    
    try:
        if not _haptic_service:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        result = await _haptic_service.stop_haptic_monitoring()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "message": "Haptic monitoring stopped",
            "status": "monitoring_inactive"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop haptic monitoring: {str(e)}")

@router.get("/status", response_model=DeviceStatus)
async def get_haptic_status():
    """
    Get current haptic mode device status
    """
    global _haptic_service
    
    try:
        if not _haptic_service:
            return DeviceStatus(
                connected=False,
                battery_level=None,
                memory_usage=None,
                last_capture=None
            )
        
        status = await _haptic_service.get_status()
        return DeviceStatus(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get haptic status: {str(e)}")

@router.post("/capture-manual", response_model=CaptureResult)
async def capture_image_manual(request: CaptureRequest):
    """
    Manually capture an image from Frame glasses (works in both modes)
    """
    global _haptic_service
    
    try:
        if not _haptic_service:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        result = await _haptic_service.capture_image(request.resolution)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return CaptureResult(
            success=True,
            image_size_bytes=result["image_size_bytes"],
            resolution=result["resolution"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to capture image: {str(e)}")

@router.post("/display")
async def display_text_haptic(text: str):
    """
    Display text on Frame glasses in haptic mode
    """
    global _haptic_service
    
    try:
        if not _haptic_service:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        result = await _haptic_service.display_text(text)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "message": result["message"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to display text: {str(e)}")

@router.post("/process-capture")
async def process_haptic_capture_with_analysis():
    """
    Process a haptic-triggered capture with vision LLM analysis and violation checking
    This endpoint simulates the complete flow: capture → analyze → check violations → send feedback
    """
    global _haptic_service
    try:
        if not _haptic_service:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        # Simulate image capture (in real implementation, this would come from the glasses)
        with open("captured_frame.jpg", "rb") as f:
            image_data = f.read()
        # Process the capture with analysis
        result = await _haptic_service.process_haptic_capture(image_data, "touch")
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return {
            "success": True,
            "message": "Haptic capture processed successfully",
            "trigger_type": result["trigger_type"],
            "image_size_bytes": result["image_size_bytes"],
            "analysis": result.get("analysis"),
            "violation_check": result.get("violation_check"),
            "feedback_message": result.get("feedback_message"),
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process haptic capture: {str(e)}")

@router.post("/test-violation-check")
async def test_violation_check(zone_number: str = "106185"):
    """
    Test violation checking for a specific zone number
    """
    global _haptic_service
    try:
        if not _haptic_service:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        # Test violation check
        violation_result = await _haptic_service._check_violations(zone_number)
        if not violation_result.get("success"):
            raise HTTPException(status_code=500, detail=violation_result.get("error"))
        # Generate feedback message
        feedback_message = _haptic_service._generate_feedback_message(violation_result)
        # Send feedback to glasses
        if feedback_message:
            await _haptic_service.display_text(feedback_message)
        return {
            "success": True,
            "zone_number": zone_number,
            "violation_count": violation_result.get("violation_count"),
            "street_name": violation_result.get("street_name"),
            "threshold_exceeded": violation_result.get("threshold_exceeded"),
            "feedback_message": feedback_message,
            "timestamp": violation_result.get("timestamp")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test violation check: {str(e)}") 