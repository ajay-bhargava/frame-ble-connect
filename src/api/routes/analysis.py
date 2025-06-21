from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import time
from typing import Optional
import re

from src.api.models.requests import AnalysisRequest, AnalysisType
from src.api.models.responses import (
    AnalysisResult, 
    CaptionResult, 
    QueryResult, 
    DetectResult, 
    PointResult
)
from src.ai.processors.moondream_processor import MoondreamProcessor

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize Moondream processor
moondream_processor = MoondreamProcessor()

@router.post("/sign")
async def analyze_sign(
    image: UploadFile = File(...),
):
    """
    Clean, focused endpoint for analyzing signs and extracting text content
    
    This endpoint is specifically designed for street signs, address signs, 
    building numbers, and other text-based signage. It extracts all readable
    text and provides a clean, structured response.
    
    Parameters:
    - image: Image file containing a sign (JPEG, PNG, GIF)
    
    Returns:
    - Simple JSON with extracted text and metadata
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Record start time for processing
        start_time = time.time()
        
        # Use focused text extraction prompt
        sign_prompt = """Extract and list ALL the actual text content you can read. Include street names, addresses, numbers, words, letters, and any written information. Format as: "Text found: [list all text content separated by commas]"."""
        
        # Perform clean sign analysis using the refactored text extraction method
        result = await moondream_processor.extract_text_from_image(image_data, sign_prompt)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Extract text from clean general analysis response
        raw_response = result.get("response", "")
        extracted_text = ""
        
        if "text found:" in raw_response.lower():
            # Extract everything after "Text found:"
            match = re.search(r"text found:\s*(.+)", raw_response, re.IGNORECASE)
            if match:
                extracted_text = match.group(1).strip()
        else:
            extracted_text = raw_response
        
        # Return clean, simple response with NO food artifacts
        return {
            "success": True,
            "extracted_text": extracted_text,
            "analysis_type": "sign_analysis",
            "processing_time_ms": processing_time_ms,
            "timestamp": result["timestamp"],
            "image_url": result.get("image_url", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sign analysis failed: {str(e)}")

# Remaining Moondream API Endpoints (Caption, Query, Detect, Point)

@router.post("/caption", response_model=CaptionResult)
async def caption_image(
    image: UploadFile = File(...),
    length: str = Form("normal"),
    stream: bool = Form(False)
):
    """
    Generate natural language descriptions of images using Moondream Caption API
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if length not in ["short", "normal"]:
        raise HTTPException(status_code=400, detail="Length must be 'short' or 'normal'")
    
    try:
        image_data = await image.read()
        start_time = time.time()
        result = await moondream_processor.caption(image_data, length=length, stream=stream)
        processing_time_ms = (time.time() - start_time) * 1000
        
        return CaptionResult(
            success=result["success"],
            caption=result.get("caption"),
            request_id=result.get("request_id"),
            length=result.get("length", ""),
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
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if len(question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        image_data = await image.read()
        start_time = time.time()
        result = await moondream_processor.query(image_data, question=question, stream=stream)
        processing_time_ms = (time.time() - start_time) * 1000
        
        return QueryResult(
            success=result["success"],
            answer=result.get("answer"),
            question=result.get("question", ""),
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
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if len(object_type.strip()) == 0:
        raise HTTPException(status_code=400, detail="Object type cannot be empty")
    
    try:
        image_data = await image.read()
        start_time = time.time()
        result = await moondream_processor.detect(image_data, object_type=object_type)
        processing_time_ms = (time.time() - start_time) * 1000
        
        return DetectResult(
            success=result["success"],
            objects=result.get("objects", []),
            object_type=result.get("object_type", ""),
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
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if len(object_type.strip()) == 0:
        raise HTTPException(status_code=400, detail="Object type cannot be empty")
        
    try:
        image_data = await image.read()
        start_time = time.time()
        result = await moondream_processor.point(image_data, object_type=object_type)
        processing_time_ms = (time.time() - start_time) * 1000
        
        return PointResult(
            success=result["success"],
            points=result.get("points", []),
            object_type=result.get("object_type", ""),
            count=result.get("count", 0),
            request_id=result.get("request_id"),
            timestamp=result["timestamp"],
            processing_time_ms=processing_time_ms,
            error_message=result.get("error") if not result["success"] else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object pointing failed: {str(e)}") 