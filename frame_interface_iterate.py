"""
Frame Interface Iterative Testing Script

This script comprehensively tests the two main functionalities of FrameInterface:
1. Tap-to-capture photo functionality (3 test scenarios)
2. Text display functionality (3 test scenarios)

The script runs each test in sequence, captures errors, asks for user validation,
and uses LLM assistance to fix issues in frame_interface.py when tests fail.

Test Architecture:
- Each test function has a clearly defined task in its docstring
- Errors are captured in error_dict with function name as key
- User validation ensures functionality actually works as expected
- LLM integration provides automated fixes when issues are detected
- Loop continues until all tests pass or manual intervention is needed

Technical Implementation:
- Uses asyncio for Frame interface operations
- Implements robust error handling and user input validation
- Provides detailed logging and status reporting
- Integrates with OpenAI API for automated debugging assistance
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Import our Frame interface
from src.connect.frame_interface import FrameInterface
import os

# For LLM integration (you'll need to install anthropic: pip install anthropic)
try:
    import anthropic  # type: ignore
    LLM_AVAILABLE = True
except ImportError:
    anthropic = None  # type: ignore
    LLM_AVAILABLE = False
    print("Warning: Anthropic not available. Install with: pip install anthropic")

# Configure logging for detailed test reporting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global error tracking dictionary
error_dict: Dict[str, str] = {}

class FrameInterfaceTester:
    """
    Comprehensive testing framework for Frame interface functionality.
    
    This class orchestrates testing of Frame glasses capabilities through
    systematic test execution, error capture, user validation, and automated
    issue resolution via LLM integration.
    """
    
    def __init__(self):
        self.interface = FrameInterface(capture_resolution=720, auto_exposure_delay=2.0)
        self.test_images: list = []
        self.test_results: Dict[str, bool] = {}
        
    async def test_basic_tap_capture(self) -> bool:
        """
        Test Case 1: Basic Tap-to-Capture Functionality
        
        SPECIFIC TASK: Verify that a single tap on Frame glasses automatically triggers
        photo capture and returns valid JPEG image data with proper metadata.
        
        Success Criteria:
        - Frame glasses connect successfully and display "Ready for taps" message
        - User can tap the glasses and see visual feedback (brief flash/indicator)
        - Photo is automatically captured within 2 seconds of tap
        - Image data is valid JPEG format with expected resolution (720p)
        - Metadata includes timestamp, resolution, and trigger source ("tap")
        
        User should observe:
        1. Frame displays "Ready for taps" text
        2. Tapping the glasses shows brief visual feedback
        3. Photo capture occurs automatically without additional input
        4. Console shows successful capture message with image size
        """
        print("\n" + "="*80)
        print("TEST 1: Basic Tap-to-Capture Functionality")
        print("="*80)
        print(self.test_basic_tap_capture.__doc__)
        
        try:
            # Set up photo capture callback
            captured_photos = []
            
            async def on_photo_captured(image_data: bytes, metadata: Dict[str, Any]):
                captured_photos.append((image_data, metadata))
                print(f"✓ Photo captured: {len(image_data)} bytes, triggered by: {metadata.get('triggered_by', 'unknown')}")
                
            async def on_tap_detected():
                print("✓ Tap detected on Frame glasses!")
                
            self.interface.set_photo_callback(on_photo_captured)
            self.interface.set_tap_callback(on_tap_detected)
            
            # Connect to Frame
            print("Connecting to Frame glasses...")
            connection_result = await self.interface.connect()
            if not connection_result["success"]:
                raise Exception(f"Connection failed: {connection_result['error']}")
                
            print("✓ Connected successfully")
            
            # Display ready message
            await self.interface.display_text("Ready for taps")
            print("Frame should now display 'Ready for taps'")
            
            # Wait for tap and capture
            print("\n👆 Please tap your Frame glasses once and wait for photo capture...")
            print("   You should see a brief visual flash when capture occurs.")
            
            # Start event loop for limited time to capture tap
            start_time = datetime.now()
            timeout_seconds = 15
            
            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                # Process events briefly
                await asyncio.sleep(0.1)
                
                # Check if we got a photo
                if captured_photos:
                    break
                    
            if not captured_photos:
                raise Exception("No photo captured within timeout period")
                
            # Validate captured photo
            image_data, metadata = captured_photos[0]
            
            if len(image_data) < 1000:  # Basic size check
                raise Exception(f"Image too small: {len(image_data)} bytes")
                
            if not image_data.startswith(b'\xff\xd8'):  # JPEG header check
                raise Exception("Invalid JPEG format")
                
            # Save test image
            image_path = self.interface.save_image(image_data, "test_basic_tap.jpg")
            self.test_images.append(image_path)
            
            print(f"✓ Test image saved: {image_path}")
            print(f"✓ Image metadata: {json.dumps(metadata, indent=2)}")
            
            return True
            
        except Exception as e:
            error_dict["test_basic_tap_capture"] = str(e)
            print(f"✗ Test failed: {e}")
            return False
            
        finally:
            # Ensure clean disconnection after test
            try:
                if self.interface.is_connected:
                    print("🔌 Disconnecting from Frame glasses...")
                    await self.interface.disconnect()
                    print("✓ Disconnected successfully")
            except Exception as disconnect_error:
                print(f"⚠️  Disconnection warning: {disconnect_error}")
            
    async def test_rapid_tap_handling(self) -> bool:
        """
        Test Case 2: Rapid Multiple Tap Handling
        
        SPECIFIC TASK: Verify that Frame interface correctly handles multiple rapid taps
        without losing captures, crashing, or creating race conditions.
        
        Success Criteria:
        - Frame can process 3 rapid taps within 5 seconds
        - Each tap generates exactly one photo capture (no duplicates)
        - No race conditions or queue overflow errors occur
        - All captured images are valid and properly sequenced
        - Memory usage remains stable throughout rapid capture sequence
        
        User should observe:
        1. Frame displays "Tap rapidly 3x" instruction
        2. Each tap shows visual feedback
        3. Each tap results in exactly one photo capture
        4. Console shows 3 distinct capture events with incrementing count
        5. No error messages or system instability
        """
        print("\n" + "="*80)
        print("TEST 2: Rapid Multiple Tap Handling")
        print("="*80)
        print(self.test_rapid_tap_handling.__doc__)
        
        try:
            captured_photos = []
            tap_count = 0
            
            async def on_photo_captured(image_data: bytes, metadata: Dict[str, Any]):
                captured_photos.append((image_data, metadata))
                print(f"✓ Rapid capture #{len(captured_photos)}: {len(image_data)} bytes")
                
            async def on_tap_detected():
                nonlocal tap_count
                tap_count += 1
                print(f"✓ Rapid tap #{tap_count} detected!")
                
            self.interface.set_photo_callback(on_photo_captured)
            self.interface.set_tap_callback(on_tap_detected)
            
            # Connect to Frame
            connection_result = await self.interface.connect()
            if not connection_result["success"]:
                raise Exception(f"Connection failed: {connection_result['error']}")
            
            # Display instruction
            await self.interface.display_text("Tap rapidly 3x")
            print("Frame should display 'Tap rapidly 3x'")
            
            print("\n👆👆👆 Please tap your Frame glasses 3 times rapidly (within 5 seconds)...")
            print("        Each tap should show visual feedback and capture a photo.")
            
            # Wait for rapid taps
            start_time = datetime.now()
            timeout_seconds = 10
            
            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                await asyncio.sleep(0.1)
                
                # Check if we got all 3 photos
                if len(captured_photos) >= 3:
                    break
                    
            if len(captured_photos) < 3:
                raise Exception(f"Only captured {len(captured_photos)} photos, expected 3")
                
            # Validate all photos are unique and valid
            for i, (image_data, metadata) in enumerate(captured_photos[:3]):
                if len(image_data) < 1000:
                    raise Exception(f"Image {i+1} too small: {len(image_data)} bytes")
                    
                if not image_data.startswith(b'\xff\xd8'):
                    raise Exception(f"Image {i+1} invalid JPEG format")
                    
                # Save test images
                image_path = self.interface.save_image(image_data, f"test_rapid_tap_{i+1}.jpg")
                self.test_images.append(image_path)
                
            print(f"✓ All 3 rapid captures successful and saved")
            print(f"✓ Total taps detected: {tap_count}")
            
            return True
            
        except Exception as e:
            error_dict["test_rapid_tap_handling"] = str(e)
            print(f"✗ Test failed: {e}")
            return False
            
        finally:
            # Ensure clean disconnection after test
            try:
                if self.interface.is_connected:
                    print("🔌 Disconnecting from Frame glasses...")
                    await self.interface.disconnect()
                    print("✓ Disconnected successfully")
            except Exception as disconnect_error:
                print(f"⚠️  Disconnection warning: {disconnect_error}")
            
    async def test_tap_with_custom_settings(self) -> bool:
        """
        Test Case 3: Tap Capture with Custom Photo Settings
        
        SPECIFIC TASK: Verify that tap-triggered photo capture respects custom
        resolution settings and capture parameters configured before connection.
        
        Success Criteria:
        - Frame interface accepts custom resolution setting (1080p instead of default 720p)
        - Tap-triggered photo capture uses the configured high resolution
        - Captured image metadata correctly reflects the custom resolution
        - Image quality and file size are appropriate for 1080p capture
        - Auto-exposure delay setting is respected for better image quality
        
        User should observe:
        1. Frame displays "High-res ready" message
        2. Tapping produces visually higher quality image than previous tests
        3. Console shows capture with 1080p resolution in metadata
        4. Saved image file is noticeably larger than 720p captures
        5. Auto-exposure delay results in better exposure quality
        """
        print("\n" + "="*80)
        print("TEST 3: Tap Capture with Custom Photo Settings")
        print("="*80)
        print(self.test_tap_with_custom_settings.__doc__)
        
        custom_interface = None
        try:
            # Disconnect current interface and create one with custom settings
            await self.interface.stop()
            
            # Create interface with high resolution settings
            custom_interface = FrameInterface(
                capture_resolution=1080,  # High resolution
                auto_exposure_delay=3.0   # Longer exposure delay
            )
            
            captured_photos = []
            
            async def on_photo_captured(image_data: bytes, metadata: Dict[str, Any]):
                captured_photos.append((image_data, metadata))
                print(f"✓ High-res photo captured: {len(image_data)} bytes at {metadata.get('resolution', 'unknown')}p")
                
            async def on_tap_detected():
                print("✓ Tap detected for high-res capture!")
                
            custom_interface.set_photo_callback(on_photo_captured)
            custom_interface.set_tap_callback(on_tap_detected)
            
            # Connect with custom settings
            print("Connecting with high-resolution settings (1080p)...")
            connection_result = await custom_interface.connect()
            if not connection_result["success"]:
                raise Exception(f"Connection failed: {connection_result['error']}")
                
            print("✓ Connected with custom settings")
            
            # Display ready message
            await custom_interface.display_text("High-res ready")
            print("Frame should display 'High-res ready'")
            
            print("\n👆 Please tap once for high-resolution capture...")
            print("   Note the longer auto-exposure delay for better quality.")
            
            # Wait for tap and capture
            start_time = datetime.now()
            timeout_seconds = 20  # Longer timeout for high-res
            
            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                await asyncio.sleep(0.1)
                
                if captured_photos:
                    break
                    
            if not captured_photos:
                raise Exception("No high-res photo captured within timeout")
                
            # Validate high-resolution capture
            image_data, metadata = captured_photos[0]
            
            if len(image_data) < 2000:  # Should be larger than 720p
                raise Exception(f"High-res image unexpectedly small: {len(image_data)} bytes")
                
            if metadata.get('resolution') != 1080:
                raise Exception(f"Wrong resolution in metadata: {metadata.get('resolution')}, expected 1080")
                
            # Save test image
            image_path = custom_interface.save_image(image_data, "test_highres_tap.jpg")
            self.test_images.append(image_path)
            
            print(f"✓ High-res test image saved: {image_path}")
            print(f"✓ Image size: {len(image_data)} bytes (should be larger than 720p captures)")
            
            return True
            
        except Exception as e:
            error_dict["test_tap_with_custom_settings"] = str(e)
            print(f"✗ Test failed: {e}")
            return False
            
        finally:
            # Ensure clean disconnection after test
            try:
                if custom_interface and custom_interface.is_connected:
                    print("🔌 Disconnecting custom interface from Frame glasses...")
                    await custom_interface.disconnect()
                    print("✓ Custom interface disconnected successfully")
            except Exception as disconnect_error:
                print(f"⚠️  Custom interface disconnection warning: {disconnect_error}")
            
            # Restore original interface
            self.interface = FrameInterface(capture_resolution=720, auto_exposure_delay=2.0)
            
    async def test_basic_text_display(self) -> bool:
        """
        Test Case 4: Basic Text Display Functionality
        
        SPECIFIC TASK: Verify that Frame interface can display simple text messages
        on the glasses screen with proper positioning and formatting.
        
        Success Criteria:
        - Frame glasses successfully display text at default position (1,1)
        - Text is clearly visible and readable on Frame display
        - Text rendering completes without errors or corruption
        - Multiple text updates work correctly (text changes as expected)
        - Text display function returns success status
        
        User should observe:
        1. Frame displays "Hello Frame!" clearly at top-left position
        2. Text is readable and properly formatted
        3. After 3 seconds, text changes to "Text test OK!"
        4. Both text messages appear crisp and correctly positioned
        5. No display artifacts or text corruption occurs
        """
        print("\n" + "="*80)
        print("TEST 4: Basic Text Display Functionality")
        print("="*80)
        print(self.test_basic_text_display.__doc__)
        
        try:
            # Ensure connection
            if not self.interface.is_connected:
                connection_result = await self.interface.connect()
                if not connection_result["success"]:
                    raise Exception(f"Connection failed: {connection_result['error']}")
                    
            # Test basic text display
            print("Displaying 'Hello Frame!' on glasses...")
            result1 = await self.interface.display_text("Hello Frame!")
            
            if not result1["success"]:
                raise Exception(f"First text display failed: {result1.get('error', 'Unknown error')}")
                
            print("✓ First text displayed successfully")
            print("Frame should now show 'Hello Frame!' at top-left")
            
            # Wait and change text
            await asyncio.sleep(3)
            
            print("Changing text to 'Text test OK!'...")
            result2 = await self.interface.display_text("Text test OK!")
            
            if not result2["success"]:
                raise Exception(f"Second text display failed: {result2.get('error', 'Unknown error')}")
                
            print("✓ Second text displayed successfully")
            print("Frame should now show 'Text test OK!'")
            
            # Validate results
            if result1.get("text_displayed") != "Hello Frame!":
                raise Exception(f"First text mismatch: got '{result1.get('text_displayed')}', expected 'Hello Frame!'")
                
            if result2.get("text_displayed") != "Text test OK!":
                raise Exception(f"Second text mismatch: got '{result2.get('text_displayed')}', expected 'Text test OK!'")
                
            print("✓ Text display validation successful")
            
            return True
            
        except Exception as e:
            error_dict["test_basic_text_display"] = str(e)
            print(f"✗ Test failed: {e}")
            return False
            
        finally:
            # Ensure clean disconnection after test
            try:
                if self.interface.is_connected:
                    print("🔌 Disconnecting from Frame glasses...")
                    await self.interface.disconnect()
                    print("✓ Disconnected successfully")
            except Exception as disconnect_error:
                print(f"⚠️  Disconnection warning: {disconnect_error}")
            
    async def test_text_positioning(self) -> bool:
        """
        Test Case 5: Text Display Positioning Control
        
        SPECIFIC TASK: Verify that Frame interface can display text at different
        positions on screen with accurate coordinate-based placement.
        
        Success Criteria:
        - Text appears at specified X,Y coordinates on Frame display
        - Multiple text elements can be positioned independently
        - Position coordinates work as expected (top-left: 1,1; center-right: 200,100)
        - Text positioning metadata is correctly returned in response
        - No overlap or collision issues between positioned text elements
        
        User should observe:
        1. Text "TOP" appears at top-left corner (position 1,1)
        2. Text "CENTER" appears in center-right area (position 200,100)  
        3. Both text elements are clearly visible simultaneously
        4. Positioning is accurate and consistent with coordinates
        5. No text overlap or display formatting issues occur
        """
        print("\n" + "="*80)
        print("TEST 5: Text Display Positioning Control")
        print("="*80)
        print(self.test_text_positioning.__doc__)
        
        try:
            # Ensure connection
            if not self.interface.is_connected:
                connection_result = await self.interface.connect()
                if not connection_result["success"]:
                    raise Exception(f"Connection failed: {connection_result['error']}")
                    
            # Test positioned text display
            print("Displaying 'TOP' at position (1,1)...")
            result1 = await self.interface.display_text("TOP", position_x=1, position_y=1)
            
            if not result1["success"]:
                raise Exception(f"First positioned text failed: {result1.get('error', 'Unknown error')}")
                
            await asyncio.sleep(2)
            
            print("Displaying 'CENTER' at position (200,100)...")  
            result2 = await self.interface.display_text("CENTER", position_x=200, position_y=100)
            
            if not result2["success"]:
                raise Exception(f"Second positioned text failed: {result2.get('error', 'Unknown error')}")
                
            print("✓ Both positioned texts displayed")
            print("Frame should show 'TOP' at top-left and 'CENTER' at center-right")
            
            # Validate positioning metadata
            if result1.get("position") != (1, 1):
                raise Exception(f"First position mismatch: got {result1.get('position')}, expected (1, 1)")
                
            if result2.get("position") != (200, 100):
                raise Exception(f"Second position mismatch: got {result2.get('position')}, expected (200, 100)")
                
            print("✓ Text positioning validation successful")
            
            return True
            
        except Exception as e:
            error_dict["test_text_positioning"] = str(e)
            print(f"✗ Test failed: {e}")
            return False
            
        finally:
            # Ensure clean disconnection after test
            try:
                if self.interface.is_connected:
                    print("🔌 Disconnecting from Frame glasses...")
                    await self.interface.disconnect()
                    print("✓ Disconnected successfully")
            except Exception as disconnect_error:
                print(f"⚠️  Disconnection warning: {disconnect_error}")
            
    async def test_long_text_truncation(self) -> bool:
        """
        Test Case 6: Long Text Truncation Handling
        
        SPECIFIC TASK: Verify that Frame interface properly handles text longer than
        display limits by truncating gracefully and providing appropriate feedback.
        
        Success Criteria:
        - Long text (>50 characters) is automatically truncated to fit Frame display
        - Truncation occurs at exactly the maximum length limit (50 chars)
        - Truncation flag is properly set in response metadata
        - Truncated text is still readable and properly formatted on display
        - Original long text and truncated version are both reported correctly
        
        User should observe:
        1. Frame displays truncated version of very long text
        2. Displayed text is exactly 50 characters (Frame's display limit)
        3. Text remains readable and properly formatted despite truncation
        4. Console shows both original and truncated text for comparison
        5. No display overflow or text rendering errors occur
        """
        print("\n" + "="*80)  
        print("TEST 6: Long Text Truncation Handling")
        print("="*80)
        print(self.test_long_text_truncation.__doc__)
        
        try:
            # Ensure connection
            if not self.interface.is_connected:
                connection_result = await self.interface.connect()
                if not connection_result["success"]:
                    raise Exception(f"Connection failed: {connection_result['error']}")
                    
            # Create very long text (exceeds 50 character limit)
            long_text = "This is a very long text message that definitely exceeds the Frame display character limit and should be truncated automatically by the interface"
            expected_truncated = long_text[:50]  # Should be truncated to 50 chars
            
            print(f"Original text length: {len(long_text)} characters")
            print(f"Expected truncated length: {len(expected_truncated)} characters")
            print(f"Testing truncation with: '{long_text}'")
            
            # Test long text display
            result = await self.interface.display_text(long_text)
            
            if not result["success"]:
                raise Exception(f"Long text display failed: {result.get('error', 'Unknown error')}")
                
            # Validate truncation behavior
            displayed_text = result.get("text_displayed", "")
            was_truncated = result.get("truncated", False)
            
            if not was_truncated:
                raise Exception("Text should have been truncated but truncation flag is False")
                
            if len(displayed_text) != 50:
                raise Exception(f"Truncated text wrong length: got {len(displayed_text)}, expected 50")
                
            if displayed_text != expected_truncated:
                raise Exception(f"Truncation mismatch: got '{displayed_text}', expected '{expected_truncated}'")
                
            print("✓ Text truncation working correctly")
            print(f"✓ Displayed text: '{displayed_text}'")
            print(f"✓ Truncation flag: {was_truncated}")
            print("Frame should show the truncated version of the long text")
            
            return True
            
        except Exception as e:
            error_dict["test_long_text_truncation"] = str(e)
            print(f"✗ Test failed: {e}")
            return False
            
        finally:
            # Ensure clean disconnection after test
            try:
                if self.interface.is_connected:
                    print("🔌 Disconnecting from Frame glasses...")
                    await self.interface.disconnect()
                    print("✓ Disconnected successfully")
            except Exception as disconnect_error:
                print(f"⚠️  Disconnection warning: {disconnect_error}")

def get_user_validation(test_name: str, test_description: Optional[str]) -> bool:
    """
    Get user confirmation that the test functionality worked as expected.
    
    Args:
        test_name: Name of the test function
        test_description: Description of what should have happened
        
    Returns:
        True if user confirms functionality worked, False otherwise
    """
    print(f"\n🔍 USER VALIDATION REQUIRED for {test_name}")
    print("="*60)
    print("Did the described functionality work as expected?")
    print("(Did you observe all the behaviors described in the test docstring?)")
    
    while True:
        response = input("\nEnter 'y' for YES (worked correctly) or 'n' for NO (didn't work): ").lower().strip()
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            issue_description = input("Please describe what happened instead: ").strip()
            error_dict[test_name] = f"User reported issue: {issue_description}"
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no")

async def call_llm_for_fixes():
    """
    Call LLM to analyze errors and suggest fixes for frame_interface.py
    
    This function sends the current error_dict to an LLM and asks for
    specific code changes to fix the identified issues.
    """
    if not LLM_AVAILABLE:
        print("❌ Anthropic not available. Please install: pip install anthropic")
        print("💡 Or manually fix the issues in frame_interface.py based on the errors:")
        for func_name, error in error_dict.items():
            print(f"   - {func_name}: {error}")
        return False
        
    if not error_dict:
        return True
        
    print("\n🤖 Calling LLM to analyze errors and suggest fixes...")
    
    # Read current frame_interface.py content
    try:
        with open("src/connect/frame_interface.py", "r") as f:
            current_code = f.read()
    except Exception as e:
        print(f"❌ Could not read frame_interface.py: {e}")
        return False
        
    # Prepare prompt for LLM
    error_summary = "\n".join([f"- {func}: {error}" for func, error in error_dict.items()])
    
    prompt = f"""
I'm testing a Frame AR glasses interface with these errors:

{error_summary}

Current frame_interface.py code:
{current_code}

Please analyze these errors and provide specific code fixes for frame_interface.py.
Focus on:
1. Connection stability and error handling
2. Tap detection and photo capture reliability  
3. Text display functionality
4. Proper async/await usage
5. Frame SDK message handling

Look at the following documentation for reference:
 https://docs.brilliant.xyz/frame/frame-sdk-lua/
 https://frame-ble-python.readthedocs.io/en/latest/api.html
 https://frame-msg-python.readthedocs.io/en/latest/api.html

Provide the corrected code sections with explanations.
"""

    try:
        # Note: You'll need to set your Anthropic API key
        # export ANTHROPIC_API_KEY="your-key-here"
        import anthropic

        client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[
                {
                    "role": "user",
                    "content": f"You are an expert Python developer specializing in Frame AR glasses SDK and async programming.\n{prompt}"
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        # Extract text from response content
        fix_suggestions = ""
        for content_block in response.content:
            try:
                # Most content blocks should have a text attribute
                fix_suggestions += getattr(content_block, 'text', '')
            except Exception:
                # Fallback for any unexpected content block types
                fix_suggestions += str(content_block)
        print("🔧 LLM Fix Suggestions:")
        print("="*60)
        print(fix_suggestions)
        
        # Ask user if they want to apply suggestions
        apply_fixes = input("\nApply these fixes automatically? (y/n): ").lower().strip()
        if apply_fixes in ['y', 'yes']:
            print("🚧 Automatic fix application not implemented yet.")
            print("💡 Please manually apply the suggested fixes to frame_interface.py")
            
        return True
        
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        print("💡 Please manually fix the issues based on the error messages")
        return False

async def main():
    """
    Main testing loop that runs all tests iteratively until they pass or manual intervention is needed.
    """
    print("🚀 Starting Frame Interface Iterative Testing")
    print("="*80)

    load_dotenv(".env.anthropic")
    
    tester = FrameInterfaceTester()
    
    # Define test functions in execution order
    test_functions = [
        tester.test_basic_tap_capture,
        tester.test_rapid_tap_handling, 
        tester.test_tap_with_custom_settings,
        tester.test_basic_text_display,
        tester.test_text_positioning,
        tester.test_long_text_truncation
    ]
    
    max_iterations = 3
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 TESTING ITERATION {iteration}/{max_iterations}")
        print("="*80)
        
        # Clear previous errors
        error_dict.clear()
        all_tests_passed = True
        
        # Run each test in sequence
        for test_func in test_functions:
            test_name = test_func.__name__
            print(f"\n▶️  Running {test_name}...")
            
            try:
                # Execute the test
                test_result = await test_func()
                
                if test_result:
                    # Test executed without exceptions - get user validation
                    user_validated = get_user_validation(test_name, test_func.__doc__)
                    
                    if user_validated:
                        print(f"✅ {test_name} PASSED")
                        tester.test_results[test_name] = True
                    else:
                        print(f"❌ {test_name} FAILED (user validation)")
                        tester.test_results[test_name] = False
                        all_tests_passed = False
                else:
                    print(f"❌ {test_name} FAILED (exception occurred)")
                    tester.test_results[test_name] = False
                    all_tests_passed = False
                    
            except Exception as e:
                error_dict[test_name] = f"Unexpected error: {str(e)}"
                print(f"❌ {test_name} FAILED (unexpected exception): {e}")
                tester.test_results[test_name] = False
                all_tests_passed = False
                
        # Print iteration summary
        print(f"\n📊 ITERATION {iteration} SUMMARY")
        print("="*40)
        passed_count = sum(1 for result in tester.test_results.values() if result)
        total_count = len(test_functions)
        
        for test_name, passed in tester.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name}: {status}")
            
        print(f"\nTests Passed: {passed_count}/{total_count}")
        
        if all_tests_passed:
            print("\n🎉 ALL TESTS PASSED! Frame interface is working correctly.")
            
            # Show captured test images
            if tester.test_images:
                print(f"\n📸 Test images saved:")
                for img_path in tester.test_images:
                    print(f"  - {img_path}")
                    
            break
        else:
            print(f"\n⚠️  Some tests failed. Errors encountered:")
            for func_name, error in error_dict.items():
                print(f"  - {func_name}: {error}")
                
            if iteration < max_iterations:
                print(f"\n🔧 Attempting to fix issues with LLM assistance...")
                fix_applied = await call_llm_for_fixes()
                
                if fix_applied:
                    print(f"📋 Please review and apply suggested fixes, then run the test again.")
                    continue_testing = input("Continue testing after fixes? (y/n): ").lower().strip()
                    if continue_testing not in ['y', 'yes']:
                        break
                else:
                    print("❌ Could not get LLM assistance. Please manually fix issues.")
                    break
            else:
                print(f"\n❌ Maximum iterations ({max_iterations}) reached.")
                print("💡 Please manually address the remaining issues in frame_interface.py")
                
    # Cleanup
    try:
        await tester.interface.stop()
    except:
        pass
        
    print("\n🏁 Testing session completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚡ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1) 