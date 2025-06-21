from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import time
from typing import Optional

from ..models.requests import AnalysisRequest, AnalysisType
from ..models.responses import AnalysisResult, FoodAnalysisResult
from ...ai.processors.moondream_processor import MoondreamProcessor

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize Moondream processor
moondream_processor = MoondreamProcessor()

@router.post("/food", response_model=FoodAnalysisResult)
async def analyze_food(
    image: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Analyze food items in the uploaded image using Moondream AI
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Perform food analysis
        result = await moondream_processor.analyze_food(image_data)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Convert to response model
        return FoodAnalysisResult(
            success=True,
            analysis_type="food_analysis",
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            result=result["structured_data"],
            food_items=[],  # TODO: Parse from structured_data
            total_calories=None,
            dietary_restrictions=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/general", response_model=AnalysisResult)
async def general_analysis(
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    Perform general image analysis with custom prompt
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Perform general analysis
        result = await moondream_processor.general_analysis(image_data, prompt)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Convert to response model
        return AnalysisResult(
            success=True,
            analysis_type="general_analysis",
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            result={"response": result["response"]}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/capture-and-analyze", response_model=FoodAnalysisResult)
async def capture_and_analyze_food(
    resolution: int = Form(720),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Capture image from Frame glasses and analyze for food items
    """
    try:
        # Import here to avoid circular imports
        from ..services.frame_service import FrameService
        
        frame_service = FrameService()
        
        # Connect to glasses
        connect_result = await frame_service.connect()
        if not connect_result["success"]:
            raise HTTPException(status_code=500, detail=connect_result["error"])
        
        try:
            # Capture image
            capture_result = await frame_service.capture_image(resolution)
            if not capture_result["success"]:
                raise HTTPException(status_code=500, detail=capture_result["error"])
            
            # Record start time for processing
            start_time = time.time()
            
            # Analyze food
            analysis_result = await moondream_processor.analyze_food(capture_result["image_data"])
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            if not analysis_result["success"]:
                raise HTTPException(status_code=500, detail=analysis_result["error"])
            
            # Display result on glasses (simplified)
            summary = analysis_result["structured_data"].get("raw_analysis", "Analysis complete")[:50]
            await frame_service.display_text(summary)
            
            # Convert to response model
            return FoodAnalysisResult(
                success=True,
                analysis_type="food_analysis",
                timestamp=analysis_result["timestamp"],
                processing_time_ms=processing_time_ms,
                result=analysis_result["structured_data"],
                food_items=[],  # TODO: Parse from structured_data
                total_calories=None,
                dietary_restrictions=[]
            )
            
        finally:
            # Always disconnect
            await frame_service.disconnect()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capture and analysis failed: {str(e)}") 