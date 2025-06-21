from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalysisResult(BaseModel):
    """Result of AI analysis - focused on signs"""
    success: bool
    analysis_type: str
    image_type: Optional[str] = "street_sign"
    timestamp: datetime
    processing_time_ms: float
    result: Dict[str, Any]
    error_message: Optional[str] = None
    
    # Text/sign-specific fields
    extracted_text: Optional[str] = None

class DeviceStatus(BaseModel):
    """Current device status"""
    connected: bool
    battery_level: Optional[int] = None
    memory_usage: Optional[str] = None
    last_capture: Optional[datetime] = None

class CaptureResult(BaseModel):
    """Result of image capture"""
    success: bool
    image_size_bytes: int
    resolution: int
    timestamp: datetime
    error_message: Optional[str] = None

# New Moondream API Response Models

class CaptionResult(BaseModel):
    """Result of image captioning"""
    success: bool
    caption: Optional[str] = None
    request_id: Optional[str] = None
    length: str
    timestamp: datetime
    processing_time_ms: float
    error_message: Optional[str] = None

class QueryResult(BaseModel):
    """Result of visual question answering"""
    success: bool
    answer: Optional[str] = None
    question: str
    request_id: Optional[str] = None
    timestamp: datetime
    processing_time_ms: float
    error_message: Optional[str] = None

class BoundingBox(BaseModel):
    """Bounding box coordinates (normalized 0-1)"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

class DetectResult(BaseModel):
    """Result of object detection"""
    success: bool
    objects: List[BoundingBox] = []
    object_type: str
    count: int
    request_id: Optional[str] = None
    timestamp: datetime
    processing_time_ms: float
    error_message: Optional[str] = None

class Point(BaseModel):
    """Point coordinates (normalized 0-1)"""
    x: float
    y: float

class PointResult(BaseModel):
    """Result of object pointing/localization"""
    success: bool
    points: List[Point] = []
    object_type: str
    count: int
    request_id: Optional[str] = None
    timestamp: datetime
    processing_time_ms: float
    error_message: Optional[str] = None 