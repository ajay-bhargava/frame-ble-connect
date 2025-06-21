from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class AnalysisType(str, Enum):
    """Types of AI analysis available"""
    FOOD_ANALYSIS = "food_analysis"
    OBJECT_DETECTION = "object_detection"
    TEXT_RECOGNITION = "text_recognition"
    SCENE_DESCRIPTION = "scene_description"

class CaptureRequest(BaseModel):
    """Request model for capturing an image"""
    resolution: Optional[int] = 720
    auto_exposure: Optional[bool] = True

class AnalysisRequest(BaseModel):
    """Request model for AI analysis"""
    image_data: bytes
    analysis_type: AnalysisType
    custom_prompt: Optional[str] = None

class StreamRequest(BaseModel):
    """Request model for starting video stream"""
    resolution: Optional[int] = 720
    fps: Optional[int] = 10 