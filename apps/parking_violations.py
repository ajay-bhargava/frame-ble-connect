"""
Parking Violations Checker for Frame AR Glasses

This application implements a comprehensive parking violations checking system that:

1. **Image Capture**: Captures images from Frame AR glasses using the Frame SDK
2. **Text Extraction**: Uses Moondream VLM via the /query API to extract zone numbers from street signs
3. **Violation Analysis**: Checks parking violation counts for the identified zone
4. **User Feedback**: Displays contextual messages on Frame glasses based on violation thresholds

## Workflow Overview:

1. Connect to Frame glasses and initialize camera/display systems
2. Capture image of parking area/street sign via glasses camera
3. Send image to `/query` API endpoint with text extraction prompt
4. Parse zone number from AI response (handles "NONE" case gracefully)
5. Query parking violations database/API for the zone
6. Compare violation count against safety threshold
7. Display appropriate message on Frame glasses with visual feedback

## Technical Implementation:

- **Frame Integration**: Uses FrameService for BLE connection and camera control
- **AI Processing**: Leverages Moondream's vision-language model for OCR/text extraction
- **Error Handling**: Comprehensive error handling for connection, capture, and analysis failures
- **User Experience**: Immediate visual feedback on glasses with clear success/warning messages
- **Extensible Design**: Modular architecture allows easy integration with real parking APIs

## Message Protocols:

- **Positive Feedback**: "don' worry abahht it 👍" - for zones with low violations
- **Warning Feedback**: "fuhgedaboutit 👎" - for zones with high violations  
- **Error Handling**: Clear error messages for various failure modes

This demonstrates practical AR application development combining computer vision,
natural language processing, and real-time user interface feedback.
"""

import asyncio
import requests
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.services.frame_msg_service import FrameService

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParkingViolationsChecker:
    """
    Complete parking violations checking system for Frame AR glasses.
    
    This class orchestrates the entire workflow from image capture through
    violation analysis to user feedback display.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000", violation_threshold: int = 5):
        """
        Initialize the parking violations checker.
        
        Args:
            api_base_url: Base URL for the analysis API server
            violation_threshold: Number of violations above which we warn the user
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.violation_threshold = violation_threshold
        self.frame_service = FrameService()
        
        # Text extraction prompt optimized for parking/street signs
        # This prompt is specifically crafted for the Moondream VLM to extract zone numbers
        self.zone_extraction_prompt = (
            "Extract the text from within the street sign in the image. "
            "Look specifically for zone numbers, parking zone identifiers, "
            "or area numbers. If you find a zone number, return just the number. "
            "If you cannot decipher it or there is no zone number visible, return 'NONE'"
        )
        
        logger.info(f"Initialized ParkingViolationsChecker with threshold: {violation_threshold}")
    
    async def extract_zone_from_image(self, image_data: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract parking zone number from captured image using Moondream VLM.
        
        This method sends the image to the /query API endpoint which uses
        Moondream's vision-language model to perform OCR and text extraction.
        
        Args:
            image_data: Raw JPEG image data from Frame glasses
            
        Returns:
            Tuple of (success: bool, zone_number: str|None, error_message: str|None)
        """
        try:
            logger.info("Sending image to analysis API for zone extraction...")
            
            # Prepare multipart form data for the /query endpoint
            # The API expects: image file + question parameter
            files = {
                'image': ('captured_frame.jpg', image_data, 'image/jpeg')
            }
            data = {
                'question': self.zone_extraction_prompt,
                'stream': False  # We want synchronous response
            }
            
            # Send request to the query endpoint
            response = requests.post(
                f"{self.api_base_url}/analysis/query",
                files=files,
                data=data,
                timeout=30  # 30 second timeout for VLM processing
            )
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return False, None, error_msg
            
            # Parse the QueryResult response
            result = response.json()
            
            if not result.get('success', False):
                error_msg = result.get('error_message', 'Unknown API error')
                logger.error(f"API analysis failed: {error_msg}")
                return False, None, error_msg
            
            # Extract the answer from the VLM
            raw_answer = result.get('answer', '').strip()
            logger.info(f"Raw VLM response: '{raw_answer}'")
            
            # Parse zone number from the response
            zone_number = self._parse_zone_from_response(raw_answer)
            
            if zone_number:
                logger.info(f"Successfully extracted zone number: {zone_number}")
                return True, zone_number, None
            else:
                logger.info("No zone number found in image")
                return True, None, "No zone number detected in image"
                
        except requests.RequestException as e:
            error_msg = f"Network error during API request: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during zone extraction: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_zone_from_response(self, response: str) -> Optional[str]:
        """
        Parse zone number from VLM response text.
        
        The VLM might return responses like:
        - "Zone 5"
        - "5"
        - "Area 12A"  
        - "NONE"
        - "I can see the number 3 on the sign"
        
        This method uses regex patterns to extract the actual zone identifier.
        
        Args:
            response: Raw text response from the VLM
            
        Returns:
            Extracted zone number/identifier or None if not found
        """
        if not response or response.upper() == 'NONE':
            return None
        
        # Check for phrases that indicate no zone was found
        negative_phrases = ['cannot make out', 'cannot see', 'no zone', 'too blurry', 'not visible']
        response_lower = response.lower()
        for phrase in negative_phrases:
            if phrase in response_lower:
                return None
        
        # Try different regex patterns for common zone number formats
        patterns = [
            r'zone\s*([a-zA-Z0-9]+)',  # "Zone 5", "zone 12A"
            r'area\s*([a-zA-Z0-9]+)',  # "Area 3", "area 12"
            r'section\s*([a-zA-Z0-9]+)',  # "Section B"
            r'\b([0-9]+[a-zA-Z]?)\b',  # Standalone numbers like "5", "12A"
            r'number\s+([a-zA-Z0-9]+)',  # "number 5" (require space to avoid matching "number" in "zone number")
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                zone = match.group(1).upper()
                logger.debug(f"Extracted zone '{zone}' using pattern '{pattern}'")
                return zone
        
        # If no patterns match, check if the entire response is just a zone identifier
        if re.match(r'^[a-zA-Z0-9]+$', response.strip()):
            return response.strip().upper()
        
        return None
    
    def get_num_violations(self, zone_number: str) -> int:
        """
        Get the number of parking violations for a specific zone.
        
        This is a placeholder implementation that demonstrates the concept.
        In a real application, this would:
        - Query a parking violations database/API
        - Connect to city parking management systems
        - Use real-time violation data from parking enforcement
        
        Args:
            zone_number: The parking zone identifier
            
        Returns:
            Number of violations in the zone (mock data for demonstration)
        """
        # Mock data for demonstration - in reality this would be a database/API call
        # Different zones have different violation patterns based on:
        # - Location desirability (downtown vs residential)
        # - Enforcement frequency
        # - Time of day/day of week patterns
        mock_violations = {
            '1': 12,   # High-traffic downtown area
            '2': 3,    # Residential area
            '3': 8,    # Business district  
            '4': 1,    # Suburban area
            '5': 15,   # Tourist area with heavy enforcement
            'A': 6,    # Mixed-use zone
            'B': 2,    # Low-traffic area
            'C': 9,    # Commercial zone
        }
        
        # Return mock data or random value for unknown zones
        violations = mock_violations.get(zone_number, 4)  # Default to moderate level
        
        logger.info(f"Zone {zone_number} has {violations} recent violations")
        return violations
    
    async def display_result_on_glasses(self, zone_number: Optional[str], 
                                       num_violations: Optional[int], 
                                       success: bool, error_msg: Optional[str]) -> bool:
        """
        Display appropriate message on Frame glasses based on violation analysis.
        
        This provides immediate visual feedback to the user with contextual information.
        
        Args:
            zone_number: Identified parking zone (if any)
            num_violations: Number of violations in the zone (if known)
            success: Whether the analysis completed successfully
            error_msg: Error message if analysis failed
            
        Returns:
            True if message was displayed successfully, False otherwise
        """
        try:
            if not success or zone_number is None:
                # Handle error cases with helpful messages
                if error_msg and "No zone number" in error_msg:
                    message = "No zone found"
                else:
                    message = "Analysis failed"
                
                logger.info(f"Displaying error message: {message}")
                result = await self.frame_service.display_text(message)
                return result.get('success', False)
            
            # Display result based on violation threshold
            if num_violations is not None and num_violations < self.violation_threshold:
                # Low violations - positive message
                message = "don' worry abahht it 👍"  # Boston accent for character
                logger.info(f"Zone {zone_number}: {num_violations} violations (safe) - showing positive message")
            else:
                # High violations - warning message  
                message = "fuhgedaboutit 👎"  # Boston accent warning
                logger.info(f"Zone {zone_number}: {num_violations} violations (risky) - showing warning message")
            
            result = await self.frame_service.display_text(message)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Failed to display result on glasses: {str(e)}")
            return False
    
    async def run_parking_check(self, resolution: int = 720) -> Dict[str, Any]:
        """
        Execute the complete parking violations checking workflow.
        
        This is the main orchestration method that coordinates all steps:
        1. Connect to Frame glasses
        2. Capture image of parking area
        3. Extract zone number using AI
        4. Look up violation count
        5. Display result on glasses
        6. Clean up connections
        
        Args:
            resolution: Image capture resolution (720, 1080, etc.)
            
        Returns:
            Dict containing complete workflow results and metadata
        """
        workflow_start = datetime.now()
        logger.info("Starting parking violations check workflow...")
        
        try:
            # Step 1: Connect to Frame glasses
            logger.info("Connecting to Frame glasses...")
            connect_result = await self.frame_service.connect()
            
            if not connect_result['success']:
                error_msg = f"Failed to connect: {connect_result['error']}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'step_failed': 'connection'
                }
            
            logger.info("✅ Connected to Frame glasses successfully")
            
            try:
                # Step 2: Capture image
                logger.info(f"Capturing image at {resolution}p resolution...")
                await self.frame_service.display_text("Capturing...")
                
                capture_result = await self.frame_service.capture_image(resolution)
                
                if not capture_result['success']:
                    error_msg = f"Image capture failed: {capture_result['error']}"
                    logger.error(error_msg)
                    await self.frame_service.display_text("Capture failed")
                    return {
                        'success': False,
                        'error': error_msg,
                        'step_failed': 'capture'
                    }
                
                image_data = capture_result['image_data']
                logger.info(f"✅ Captured image: {len(image_data)} bytes")
                
                # Step 3: Extract zone number using AI
                logger.info("Analyzing image for zone number...")
                await self.frame_service.display_text("Analyzing...")
                
                extract_success, zone_number, extract_error = await self.extract_zone_from_image(image_data)
                
                # Step 4 & 5: Get violations and display result
                num_violations = None
                if extract_success and zone_number:
                    num_violations = self.get_num_violations(zone_number)
                
                # Display result on glasses
                display_success = await self.display_result_on_glasses(
                    zone_number, num_violations, extract_success, extract_error
                )
                
                # Calculate total processing time
                processing_time = (datetime.now() - workflow_start).total_seconds()
                
                # Compile comprehensive results
                result = {
                    'success': extract_success,
                    'timestamp': workflow_start.isoformat(),
                    'processing_time_seconds': processing_time,
                    'zone_number': zone_number,
                    'num_violations': num_violations,
                    'threshold': self.violation_threshold,
                    'recommendation': 'safe' if (num_violations and num_violations < self.violation_threshold) else 'risky',
                    'image_size_bytes': len(image_data),
                    'resolution': resolution,
                    'display_success': display_success
                }
                
                if not extract_success:
                    result['error'] = extract_error
                    result['step_failed'] = 'analysis'
                
                logger.info(f"✅ Workflow completed in {processing_time:.2f}s")
                return result
                
            finally:
                # Step 6: Always disconnect cleanly
                logger.info("Disconnecting from Frame glasses...")
                await self.frame_service.disconnect()
                
        except Exception as e:
            error_msg = f"Unexpected workflow error: {str(e)}"
            logger.error(error_msg)
            
            # Attempt cleanup on error
            try:
                await self.frame_service.disconnect()
            except:
                pass
                
            return {
                'success': False,
                'error': error_msg,
                'step_failed': 'unexpected_error',
                'timestamp': workflow_start.isoformat()
            }


async def main():
    """
    Example usage demonstrating the parking violations checker.
    
    This function shows how to use the ParkingViolationsChecker class
    and provides a complete working example.
    """
    # Initialize the checker with custom settings
    checker = ParkingViolationsChecker(
        api_base_url="http://localhost:8000",  # Adjust for your API server
        violation_threshold=5  # Warn if more than 5 violations
    )
    
    print("🚗 Parking Violations Checker for Frame AR Glasses")
    print("=" * 50)
    print("This demo will:")
    print("1. Connect to your Frame glasses")
    print("2. Capture an image of a parking area/street sign")
    print("3. Use AI to extract the zone number")
    print("4. Check violation count for that zone") 
    print("5. Display recommendation on glasses")
    print()
    
    try:
        # Run the complete workflow
        result = await checker.run_parking_check(resolution=1080)
        
        # Display results
        print("📊 RESULTS")
        print("-" * 20)
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"Zone Number: {result['zone_number']}")
            print(f"Violations: {result['num_violations']}")
            print(f"Threshold: {result['threshold']}")
            print(f"Recommendation: {result['recommendation'].upper()}")
            print(f"Processing Time: {result['processing_time_seconds']:.2f}s")
            print(f"Image Size: {result['image_size_bytes']} bytes")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Failed at: {result.get('step_failed', 'Unknown step')}")
        
        print(f"Completed at: {result['timestamp']}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())