# pylint: disable=import-error
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from src.ai.processors.moondream_processor import MoondreamProcessor  # pylint: disable=import-error
from src.api.services.parking_service import ParkingService  # pylint: disable=import-error

router = APIRouter(prefix="/parking", tags=["parking"])

# Initialize services
moondream_processor = MoondreamProcessor()
parking_service = ParkingService()

@router.post("/analyze-sign")
async def analyze_parking_sign(
    image: UploadFile = File(...),
    include_violations: bool = True
):
    """
    Analyze a parking sign image and get parking information and violation statistics
    
    This endpoint:
    1. Uses AI to extract text from the parking sign
    2. Parses zone number and street name from the text
    3. Queries NYC parking meter data
    4. Returns violation statistics for the location
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"parking_sign_{timestamp}_{hash(image_data) % 10000:04x}.jpg"
        
        # Step 1: Extract text from image using AI
        print(f"🔍 Analyzing parking sign image: {filename}")
        
        # Use specialized prompt for parking sign text extraction
        parking_sign_prompt = """Extract ALL text from this parking sign. Look for:
1. Zone numbers (pay-by-cell numbers) - usually 5-6 digits
2. Street names and addresses
3. Parking restrictions and hours
4. Any other text on the sign

Format your response as: "Text found: [list all text content separated by commas]"
Be thorough and include every piece of text you can read."""
        
        # Perform text extraction
        text_result = await moondream_processor.extract_text_from_image(
            image_data, 
            parking_sign_prompt
        )
        
        if not text_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to extract text from image: {text_result.get('error', 'Unknown error')}"
            )
        
        # Extract the OCR text
        ocr_text = text_result.get("response", "")
        if not ocr_text:
            raise HTTPException(status_code=500, detail="No text extracted from image")
        
        print(f"📝 Extracted text: {ocr_text}")
        
        # Step 2: Analyze parking sign and get parking information
        parking_analysis = await parking_service.analyze_parking_sign(ocr_text)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Prepare response
        response_data = {
            "success": True,
            "analysis_type": "parking_sign_analysis",
            "image_type": "street_sign",
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time_ms,
            "ocr_text": ocr_text,
            "extracted_data": parking_analysis.get("extracted_data", {}),
            "parking_info": parking_analysis.get("parking_info"),
            "violation_stats": parking_analysis.get("violation_stats") if include_violations else None,
            "image_filename": filename,
            "image_url": f"http://localhost:8000/static/images/{filename}"
        }
        
        return JSONResponse(content=response_data)
        
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        processing_time_ms = (time.time() - start_time) * 1000
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/zone/{zone_number}")
async def get_parking_info_by_zone(zone_number: str):
    """
    Get parking meter information by zone number
    """
    try:
        result = await parking_service.get_parking_info_by_zone(zone_number)
        return JSONResponse(content=result)
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get parking info: {str(e)}"
            }
        )

@router.get("/street/{street_name}")
async def get_parking_info_by_street(street_name: str):
    """
    Get parking meter information by street name
    """
    try:
        result = await parking_service.get_parking_info_by_street(street_name)
        return JSONResponse(content=result)
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get parking info: {str(e)}"
            }
        )

@router.post("/extract-text")
async def extract_text_from_sign(
    image: UploadFile = File(...)
):
    """
    Extract text from a parking sign image (text extraction only)
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"text_extract_{timestamp}_{hash(image_data) % 10000:04x}.jpg"
        
        # Extract text using AI
        parking_sign_prompt = """Extract ALL text from this parking sign. Look for:
1. Zone numbers (pay-by-cell numbers) - usually 5-6 digits
2. Street names and addresses
3. Parking restrictions and hours
4. Any other text on the sign

Format your response as: "Text found: [list all text content separated by commas]"
Be thorough and include every piece of text you can read."""
        
        result = await moondream_processor.extract_text_from_image(
            image_data, 
            parking_sign_prompt
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return JSONResponse(content={
            "success": result.get("success", False),
            "ocr_text": result.get("response", ""),
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now().isoformat(),
            "image_filename": filename,
            "image_url": f"http://localhost:8000/static/images/{filename}"
        })
        
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        processing_time_ms = (time.time() - start_time) * 1000
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Text extraction failed: {str(e)}",
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/violations-by-zone/{zone_number}")
async def get_violations_by_zone(zone_number: str):
    """
    Get parking violations count by zone number (pay-by-cell number)
    
    This endpoint:
    1. Gets the street address from the zone number
    2. Uses that address to get the violation count
    
    ⚠️  Note: Violation data is historical from 2023, not real-time current data.
    
    Args:
        zone_number: The pay-by-cell number (e.g., "106184")
        
    Returns:
        Complete analysis with zone info, address, and violation count
    """
    try:
        local_parking_service = ParkingService()
        result = await local_parking_service.get_violations_by_zone(zone_number)
        await local_parking_service.close()
        return result
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        return {
            "success": False,
            "error": f"Failed to get violations by zone: {str(e)}",
            "zone_number": zone_number,
            "timestamp": datetime.now().isoformat()
        }

@router.get("/violations-by-street/{street_name}")
async def get_violations_by_street(street_name: str):
    """
    Get parking violations count for a street name
    
    ⚠️  Note: Violation data is historical from 2023, not real-time current data.
    
    Args:
        street_name: The street name (e.g., "LITTLE WEST 12 STREET")
        
    Returns:
        Violation count and metadata
    """
    try:
        local_parking_service = ParkingService()
        result = await local_parking_service.get_violation_count_by_street(street_name)
        await local_parking_service.close()
        return result
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        return {
            "success": False,
            "error": f"Failed to get violations by street: {str(e)}",
            "street_name": street_name,
            "timestamp": datetime.now().isoformat()
        }

@router.get("/violation-count/{zone_number}")
async def get_violation_count_by_zone(zone_number: str):
    """
    Get just the violation count for a zone number (pay-by-cell number)
    
    This endpoint:
    1. Gets the street address from the zone number
    2. Uses that address to get the violation count
    3. Returns a simplified response with just the count
    
    ⚠️  Note: Violation data is historical from 2023, not real-time current data.
    
    Args:
        zone_number: The pay-by-cell number (e.g., "106184")
        
    Returns:
        Simplified response with zone number, street name, and violation count
    """
    try:
        local_parking_service = ParkingService()
        result = await local_parking_service.get_violation_count_by_zone(zone_number)
        await local_parking_service.close()
        return result
    except (ValueError, OSError, RuntimeError) as e:  # pylint: disable=broad-except
        return {
            "success": False,
            "error": f"Failed to get violation count by zone: {str(e)}",
            "zone_number": zone_number,
            "timestamp": datetime.now().isoformat()
        } 