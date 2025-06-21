from fastapi import APIRouter, HTTPException
from typing import Optional

from ..models.requests import CaptureRequest
from ..models.responses import DeviceStatus, CaptureResult

router = APIRouter(prefix="/device", tags=["device"])

@router.get("/status", response_model=DeviceStatus)
async def get_device_status():
    """
    Get current Frame glasses device status
    """
    try:
        from ..services.frame_service import FrameService
        
        frame_service = FrameService()
        status = await frame_service.get_status()
        
        return DeviceStatus(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device status: {str(e)}")

@router.post("/connect")
async def connect_device():
    """
    Connect to Frame glasses
    """
    try:
        from ..services.frame_service import FrameService
        
        frame_service = FrameService()
        result = await frame_service.connect()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "message": result["message"],
            "battery_memory": result.get("battery_memory")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")

@router.post("/disconnect")
async def disconnect_device():
    """
    Disconnect from Frame glasses
    """
    try:
        from ..services.frame_service import FrameService
        
        frame_service = FrameService()
        await frame_service.disconnect()
        
        return {
            "success": True,
            "message": "Disconnected from Frame glasses"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

@router.post("/capture", response_model=CaptureResult)
async def capture_image(request: CaptureRequest):
    """
    Capture an image from Frame glasses
    """
    try:
        from ..services.frame_service import FrameService
        
        frame_service = FrameService()
        
        # Connect if not already connected
        connect_result = await frame_service.connect()
        if not connect_result["success"]:
            raise HTTPException(status_code=500, detail=connect_result["error"])
        
        try:
            # Capture image
            result = await frame_service.capture_image(request.resolution)
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return CaptureResult(
                success=True,
                image_size_bytes=result["image_size_bytes"],
                resolution=result["resolution"],
                timestamp=result["timestamp"]
            )
            
        finally:
            # Always disconnect
            await frame_service.disconnect()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to capture image: {str(e)}")

@router.post("/display")
async def display_text(text: str):
    """
    Display text on Frame glasses
    """
    try:
        from ..services.frame_service import FrameService
        
        frame_service = FrameService()
        
        # Connect if not already connected
        connect_result = await frame_service.connect()
        if not connect_result["success"]:
            raise HTTPException(status_code=500, detail=connect_result["error"])
        
        try:
            # Display text
            result = await frame_service.display_text(text)
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return {
                "success": True,
                "message": result["message"]
            }
            
        finally:
            # Always disconnect
            await frame_service.disconnect()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to display text: {str(e)}") 