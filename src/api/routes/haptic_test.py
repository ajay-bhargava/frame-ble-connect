from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio

from src.connect.haptic_detector import HapticDetector

router = APIRouter(prefix="/haptic-test", tags=["haptic-test"])

# Global haptic detector instance
_haptic_detector = None

@router.post("/connect")
async def connect_haptic_detector():
    """
    Connect to Frame glasses using the haptic detector
    """
    global _haptic_detector
    
    try:
        _haptic_detector = HapticDetector()
        result = await _haptic_detector.connect_to_glasses()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "message": "Connected to Frame glasses with haptic detector",
            "timestamp": result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")

@router.post("/start-monitoring")
async def start_haptic_monitoring():
    """
    Start monitoring for light tap events
    """
    global _haptic_detector
    
    try:
        if not _haptic_detector:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        async def touch_callback(data: Dict[str, Any]):
            """Callback for touch events"""
            print(f"🎯 Touch detected via API: {data}")
        
        result = await _haptic_detector.start_touch_monitoring(touch_callback)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "message": "Light tap monitoring started",
            "monitoring_active": True,
            "sensitivity": "light_tap",
            "timestamp": result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/stop-monitoring")
async def stop_haptic_monitoring():
    """
    Stop monitoring for light tap events
    """
    global _haptic_detector
    
    try:
        if not _haptic_detector:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        result = await _haptic_detector.stop_touch_monitoring()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "message": "Light tap monitoring stopped",
            "monitoring_active": False,
            "timestamp": result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/status")
async def get_haptic_detector_status():
    """
    Get current haptic detector status
    """
    global _haptic_detector
    
    try:
        if not _haptic_detector:
            return {
                "connected": False,
                "monitoring_active": False,
                "message": "No haptic detector instance"
            }
        
        status = _haptic_detector.get_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/test-tap")
async def test_tap_detection():
    """
    Test tap detection by simulating a tap event
    """
    global _haptic_detector
    
    try:
        if not _haptic_detector:
            raise HTTPException(status_code=400, detail="Not connected to Frame glasses")
        
        # Simulate a tap event
        async def test_callback(data: Dict[str, Any]):
            print(f"🧪 Test tap detected: {data}")
        
        # Temporarily set callback and trigger
        original_callback = _haptic_detector.touch_callback
        _haptic_detector.touch_callback = test_callback
        
        # Simulate tap detection
        await _haptic_detector._handle_touch_detected()
        
        # Restore original callback
        _haptic_detector.touch_callback = original_callback
        
        return {
            "success": True,
            "message": "Test tap event triggered",
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test tap: {str(e)}")

@router.post("/disconnect")
async def disconnect_haptic_detector():
    """
    Disconnect from Frame glasses
    """
    global _haptic_detector
    
    try:
        if not _haptic_detector:
            return {
                "success": True,
                "message": "No connection to disconnect"
            }
        
        result = await _haptic_detector.disconnect()
        _haptic_detector = None
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "message": "Disconnected from Frame glasses",
            "timestamp": result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}") 