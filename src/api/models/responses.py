from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class FoodItem(BaseModel):
    """Individual food item detected"""
    name: str
    confidence: float
    calories: Optional[int] = None
    nutrients: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    """Result of AI analysis"""
    success: bool
    analysis_type: str
    timestamp: datetime
    processing_time_ms: float
    result: Dict[str, Any]
    error_message: Optional[str] = None

class FoodAnalysisResult(AnalysisResult):
    """Specific result for food analysis"""
    food_items: List[FoodItem]
    total_calories: Optional[int] = None
    dietary_restrictions: Optional[List[str]] = None

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