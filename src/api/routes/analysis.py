from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import time
from typing import Optional

from src.api.models.requests import AnalysisRequest, AnalysisType
from src.api.models.responses import (
    AnalysisResult, 
    FoodAnalysisResult, 
    CaptionResult, 
    QueryResult, 
    DetectResult, 
    PointResult
)
from src.ai.processors.moondream_processor import MoondreamProcessor

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize Moondream processor
moondream_processor = MoondreamProcessor()

@router.post("/upload-and-analyze", response_model=FoodAnalysisResult)
async def upload_and_analyze_food(
    image: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Upload an image and analyze it using Moondream AI with optional custom prompt
    
    Examples:
    - Food analysis: Leave custom_prompt empty or use "What food is shown in this image?"
    - Text reading: "Read all the text visible in this image"
    - Street signs: "What street signs or addresses are visible in this image?"
    - Menu reading: "Read the menu items and prices shown in this image"
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Perform analysis with custom prompt
        result = await moondream_processor.analyze_food(image_data, custom_prompt)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Convert to response model
        return FoodAnalysisResult(
            success=True,
            analysis_type=result["structured_data"].get("analysis_type", "food_analysis"),
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            result=result["structured_data"],
            food_items=[],  # TODO: Parse from structured_data
            total_calories=None,
            dietary_restrictions=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/upload-and-find-restaurant")
async def upload_and_find_restaurant(
    image: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Complete workflow: Upload image → Analyze food → Find restaurant → Return maps link
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Import restaurant service
        from src.api.services.restaurant_service import RestaurantService
        
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Step 1: Analyze food
        food_result = await moondream_processor.analyze_food(image_data, custom_prompt)
        
        if not food_result["success"]:
            raise HTTPException(status_code=500, detail=f"Food analysis failed: {food_result['error']}")
        
        # Step 2: Find restaurant
        restaurant_service = RestaurantService()
        primary_food = food_result.get("primary_food_item", "unknown")
        
        if primary_food == "unknown":
            # Try to extract from structured data
            structured_data = food_result.get("structured_data", {})
            primary_food = structured_data.get("primary_food_item", "food")
        
        restaurant_result = await restaurant_service.find_restaurant_for_food(primary_food)
        
        # Calculate total processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Combine results
        combined_result = {
            "success": True,
            "food_analysis": food_result,
            "restaurant_found": restaurant_result["success"],
            "restaurant": restaurant_result.get("restaurant", {}),
            "maps_link": restaurant_result.get("maps_link", ""),
            "primary_food_item": primary_food,
            "processing_time_ms": processing_time_ms,
            "timestamp": food_result["timestamp"]
        }
        
        return combined_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Food-to-restaurant analysis failed: {str(e)}")

@router.post("/general", response_model=AnalysisResult)
async def general_analysis(
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    Perform general image analysis with custom prompt
    """
    if not image.content_type or not image.content_type.startswith('image/'):
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
        from src.api.services.frame_service import FrameService
        
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
            analysis_result = await moondream_processor.analyze_food(capture_result["image_data"], custom_prompt)
            
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

@router.post("/capture-and-find-restaurant")
async def capture_and_find_restaurant(
    resolution: int = Form(720),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Complete workflow: Capture from glasses → Analyze food → Find restaurant → Display on glasses
    """
    try:
        # Import services
        from src.api.services.frame_service import FrameService
        from src.api.services.restaurant_service import RestaurantService
        
        frame_service = FrameService()
        restaurant_service = RestaurantService()
        
        # Connect to glasses
        connect_result = await frame_service.connect()
        if not connect_result["success"]:
            raise HTTPException(status_code=500, detail=connect_result["error"])
        
        try:
            # Step 1: Capture image
            capture_result = await frame_service.capture_image(resolution)
            if not capture_result["success"]:
                raise HTTPException(status_code=500, detail=capture_result["error"])
            
            # Step 2: Analyze food
            start_time = time.time()
            food_result = await moondream_processor.analyze_food(capture_result["image_data"], custom_prompt)
            
            if not food_result["success"]:
                raise HTTPException(status_code=500, detail=f"Food analysis failed: {food_result['error']}")
            
            # Step 3: Find restaurant
            primary_food = food_result.get("primary_food_item", "unknown")
            if primary_food == "unknown":
                structured_data = food_result.get("structured_data", {})
                primary_food = structured_data.get("primary_food_item", "food")
            
            restaurant_result = await restaurant_service.find_restaurant_for_food(primary_food)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Step 4: Display results on glasses
            if restaurant_result["success"]:
                restaurant = restaurant_result["restaurant"]
                display_text = f"{restaurant['name']} - {restaurant['address']}"
                await frame_service.display_text(display_text[:50])  # Truncate for display
            else:
                await frame_service.display_text(f"Found {primary_food} restaurant")
            
            # Return combined results
            return {
                "success": True,
                "food_analysis": food_result,
                "restaurant_found": restaurant_result["success"],
                "restaurant": restaurant_result.get("restaurant", {}),
                "maps_link": restaurant_result.get("maps_link", ""),
                "primary_food_item": primary_food,
                "processing_time_ms": processing_time_ms,
                "timestamp": food_result["timestamp"]
            }
            
        finally:
            # Always disconnect
            await frame_service.disconnect()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capture and restaurant search failed: {str(e)}")

# Backward compatibility aliases
@router.post("/food", response_model=FoodAnalysisResult)
async def food_alias(
    image: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Alias for /upload-and-analyze - Upload an image and analyze food items
    """
    return await upload_and_analyze_food(image, custom_prompt)

@router.post("/food-to-restaurant")
async def food_to_restaurant_alias(
    image: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Alias for /upload-and-find-restaurant - Upload image → Analyze → Find restaurant
    """
    return await upload_and_find_restaurant(image, custom_prompt)

# New Moondream API Endpoints

@router.post("/caption", response_model=CaptionResult)
async def caption_image(
    image: UploadFile = File(...),
    length: str = Form("normal"),
    stream: bool = Form(False)
):
    """
    Generate natural language descriptions of images using Moondream Caption API
    
    This endpoint analyzes an image and returns descriptive captions, from brief summaries 
    to detailed explanations of visual content. Useful for generating alt text for 
    accessibility, content indexing, and automated documentation.
    
    Parameters:
    - image: Image file to analyze (JPEG, PNG, GIF)
    - length: Caption detail level - "short" for 1-2 sentence summary or "normal" for detailed description
    - stream: Whether to stream the response token by token (currently not supported in this endpoint)
    
    Returns:
    - CaptionResult with generated caption text and metadata
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if length not in ["short", "normal"]:
        raise HTTPException(status_code=400, detail="Length must be 'short' or 'normal'")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Generate caption
        result = await moondream_processor.caption(image_data, length=length, stream=stream)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert to response model
        return CaptionResult(
            success=result["success"],
            caption=result.get("caption"),
            request_id=result.get("request_id"),
            length=result["length"],
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            error_message=result.get("error") if not result["success"] else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")

@router.post("/query", response_model=QueryResult)
async def query_image(
    image: UploadFile = File(...),
    question: str = Form(...),
    stream: bool = Form(False)
):
    """
    Ask natural language questions about images using Moondream Query API (VQA)
    
    This endpoint enables Visual Question Answering - you can ask specific questions
    about image content and receive detailed answers. More focused than general
    captioning, this is ideal for extracting specific information from images.
    
    Parameters:
    - image: Image file to analyze (JPEG, PNG, GIF)
    - question: Natural language question to ask about the image (max 512 characters)
    - stream: Whether to stream the response token by token (currently not supported)
    
    Returns:
    - QueryResult with AI-generated answer and metadata
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if len(question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(question) > 512:
        raise HTTPException(status_code=400, detail="Question must be 512 characters or less")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Ask question about image
        result = await moondream_processor.query(image_data, question=question, stream=stream)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert to response model
        return QueryResult(
            success=result["success"],
            answer=result.get("answer"),
            question=result["question"],
            request_id=result.get("request_id"),
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            error_message=result.get("error") if not result["success"] else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual question answering failed: {str(e)}")

@router.post("/detect", response_model=DetectResult)
async def detect_objects(
    image: UploadFile = File(...),
    object_type: str = Form(...)
):
    """
    Detect and locate specific objects in images using Moondream Detect API
    
    This endpoint identifies objects and returns bounding box coordinates for each
    detected instance. Uses zero-shot detection, meaning it can detect virtually
    any object you specify. Coordinates are normalized (0-1) relative to image size.
    
    Parameters:
    - image: Image file to analyze (JPEG, PNG, GIF)
    - object_type: Type of object to detect (e.g., "person", "car", "face", "food")
    
    Returns:
    - DetectResult with bounding boxes for detected objects
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if len(object_type.strip()) == 0:
        raise HTTPException(status_code=400, detail="Object type cannot be empty")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Detect objects
        result = await moondream_processor.detect(image_data, object_type=object_type)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert to response model
        return DetectResult(
            success=result["success"],
            objects=result.get("objects", []),
            object_type=result["object_type"],
            count=result.get("count", 0),
            request_id=result.get("request_id"),
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            error_message=result.get("error") if not result["success"] else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")

@router.post("/point", response_model=PointResult)
async def point_objects(
    image: UploadFile = File(...),
    object_type: str = Form(...)
):
    """
    Get precise center point coordinates for objects using Moondream Point API
    
    Unlike detect() which returns bounding boxes, this endpoint returns center points
    for each instance of the specified object. Useful for precise targeting, UI
    interactions, or when you need exact object locations rather than full bounds.
    
    Parameters:
    - image: Image file to analyze (JPEG, PNG, GIF)
    - object_type: Type of object to locate (e.g., "person", "car", "face", "button")
    
    Returns:
    - PointResult with center coordinates for detected objects
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if len(object_type.strip()) == 0:
        raise HTTPException(status_code=400, detail="Object type cannot be empty")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Get object center points
        result = await moondream_processor.point(image_data, object_type=object_type)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert to response model
        return PointResult(
            success=result["success"],
            points=result.get("points", []),
            object_type=result["object_type"],
            count=result.get("count", 0),
            request_id=result.get("request_id"),
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            error_message=result.get("error") if not result["success"] else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object pointing failed: {str(e)}") 