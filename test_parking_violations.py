"""
Comprehensive test suite for the Parking Violations Checker

This test suite validates the complete parking violations workflow including:
- API integration with the /query endpoint
- Zone number parsing from VLM responses
- Frame glasses integration
- Error handling and edge cases
- Mock violation data processing

Tests use pytest fixtures and mocking to simulate Frame hardware and API responses
without requiring actual hardware or network connections.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.parking_violations import ParkingViolationsChecker


class TestParkingViolationsChecker:
    """Test suite for the ParkingViolationsChecker class"""
    
    @pytest.fixture
    def checker(self):
        """Create a parking violations checker instance for testing"""
        return ParkingViolationsChecker(
            api_base_url="http://localhost:8000",
            violation_threshold=5
        )
    
    @pytest.fixture
    def mock_frame_service(self):
        """Mock Frame service for testing without hardware"""
        mock_service = AsyncMock()
        
        # Mock successful connection
        mock_service.connect.return_value = {
            'success': True,
            'battery_memory': '85 / 42.3',
            'message': 'Connected to Frame glasses'
        }
        
        # Mock successful image capture
        mock_service.capture_image.return_value = {
            'success': True,
            'image_data': b'fake_jpeg_data_for_zone_5',
            'image_size_bytes': 1024,
            'resolution': 720,
            'timestamp': '2024-01-01T12:00:00'
        }
        
        # Mock successful text display
        mock_service.display_text.return_value = {
            'success': True,
            'message': 'Displayed: test message'
        }
        
        # Mock successful disconnect
        mock_service.disconnect.return_value = None
        
        return mock_service
    
    def test_initialization(self, checker):
        """Test proper initialization of the checker"""
        assert checker.api_base_url == "http://localhost:8000"
        assert checker.violation_threshold == 5
        assert "zone number" in checker.zone_extraction_prompt.lower()
        assert "none" in checker.zone_extraction_prompt.lower()
    
    def test_parse_zone_from_response_simple_number(self, checker):
        """Test parsing simple zone numbers from VLM responses"""
        # Test simple number response
        assert checker._parse_zone_from_response("5") == "5"
        assert checker._parse_zone_from_response("12") == "12"
        assert checker._parse_zone_from_response("3A") == "3A"
    
    def test_parse_zone_from_response_with_text(self, checker):
        """Test parsing zone numbers from descriptive responses"""
        # Test responses with surrounding text
        assert checker._parse_zone_from_response("Zone 5") == "5"
        assert checker._parse_zone_from_response("I can see zone 12A on the sign") == "12A"
        assert checker._parse_zone_from_response("Area 3 is visible") == "3"
        assert checker._parse_zone_from_response("Section B") == "B"
        assert checker._parse_zone_from_response("The number 7 is on the sign") == "7"
    
    def test_parse_zone_from_response_none_cases(self, checker):
        """Test handling of 'NONE' and empty responses"""
        assert checker._parse_zone_from_response("NONE") is None
        assert checker._parse_zone_from_response("none") is None
        assert checker._parse_zone_from_response("") is None
        assert checker._parse_zone_from_response("No zone number visible") is None
        assert checker._parse_zone_from_response("I cannot see any numbers") is None
    
    def test_get_num_violations_known_zones(self, checker):
        """Test violation count retrieval for known zones"""
        # Test known zones from mock data
        assert checker.get_num_violations('1') == 12  # High-traffic downtown
        assert checker.get_num_violations('2') == 3   # Residential
        assert checker.get_num_violations('5') == 15  # Tourist area
        assert checker.get_num_violations('A') == 6   # Mixed-use
        assert checker.get_num_violations('B') == 2   # Low-traffic
    
    def test_get_num_violations_unknown_zones(self, checker):
        """Test violation count for unknown zones (default behavior)"""
        # Unknown zones should return default value of 4
        assert checker.get_num_violations('Z') == 4
        assert checker.get_num_violations('99') == 4
        assert checker.get_num_violations('UNKNOWN') == 4
    
    @pytest.mark.asyncio
    async def test_display_result_safe_zone(self, checker, mock_frame_service):
        """Test display message for safe zones (low violations)"""
        checker.frame_service = mock_frame_service
        
        result = await checker.display_result_on_glasses(
            zone_number="2", 
            num_violations=3, 
            success=True, 
            error_msg=None
        )
        
        assert result is True
        mock_frame_service.display_text.assert_called_with("don' worry abahht it 👍")
    
    @pytest.mark.asyncio
    async def test_display_result_risky_zone(self, checker, mock_frame_service):
        """Test display message for risky zones (high violations)"""
        checker.frame_service = mock_frame_service
        
        result = await checker.display_result_on_glasses(
            zone_number="5", 
            num_violations=15, 
            success=True, 
            error_msg=None
        )
        
        assert result is True
        mock_frame_service.display_text.assert_called_with("fuhgedaboutit 👎")
    
    @pytest.mark.asyncio
    async def test_display_result_no_zone_found(self, checker, mock_frame_service):
        """Test display message when no zone is detected"""
        checker.frame_service = mock_frame_service
        
        result = await checker.display_result_on_glasses(
            zone_number=None, 
            num_violations=None, 
            success=True, 
            error_msg="No zone number detected in image"
        )
        
        assert result is True
        mock_frame_service.display_text.assert_called_with("No zone found")
    
    @pytest.mark.asyncio
    async def test_display_result_analysis_failed(self, checker, mock_frame_service):
        """Test display message when analysis fails"""
        checker.frame_service = mock_frame_service
        
        result = await checker.display_result_on_glasses(
            zone_number=None, 
            num_violations=None, 
            success=False, 
            error_msg="API request failed"
        )
        
        assert result is True
        mock_frame_service.display_text.assert_called_with("Analysis failed")
    
    @pytest.mark.asyncio
    @patch('apps.parking_violations.requests.post')
    async def test_extract_zone_successful(self, mock_post, checker):
        """Test successful zone extraction from API"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'answer': 'Zone 5',
            'question': checker.zone_extraction_prompt,
            'timestamp': '2024-01-01T12:00:00',
            'processing_time_ms': 1500.0
        }
        mock_post.return_value = mock_response
        
        success, zone_number, error = await checker.extract_zone_from_image(b'fake_image_data')
        
        assert success is True
        assert zone_number == "5"
        assert error is None
        
        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:8000/analysis/query"
        assert 'files' in kwargs
        assert 'data' in kwargs
        assert kwargs['data']['question'] == checker.zone_extraction_prompt
    
    @pytest.mark.asyncio
    @patch('apps.parking_violations.requests.post')
    async def test_extract_zone_api_failure(self, mock_post, checker):
        """Test handling of API failures"""
        # Mock API failure
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        success, zone_number, error = await checker.extract_zone_from_image(b'fake_image_data')
        
        assert success is False
        assert zone_number is None
        assert "500" in error
        assert "Internal Server Error" in error
    
    @pytest.mark.asyncio
    @patch('apps.parking_violations.requests.post')
    async def test_extract_zone_no_zone_found(self, mock_post, checker):
        """Test handling when no zone is found in image"""
        # Mock API response with NONE result
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'answer': 'NONE',
            'question': checker.zone_extraction_prompt,
            'timestamp': '2024-01-01T12:00:00',
            'processing_time_ms': 1200.0
        }
        mock_post.return_value = mock_response
        
        success, zone_number, error = await checker.extract_zone_from_image(b'fake_image_data')
        
        assert success is True
        assert zone_number is None
        assert "No zone number detected" in error
    
    @pytest.mark.asyncio
    async def test_run_parking_check_complete_workflow(self, checker, mock_frame_service):
        """Test the complete parking check workflow"""
        checker.frame_service = mock_frame_service
        
        # Mock the zone extraction method
        async def mock_extract_zone(image_data):
            return True, "2", None  # Safe zone with 3 violations
        
        checker.extract_zone_from_image = mock_extract_zone
        
        result = await checker.run_parking_check(resolution=1080)
        
        # Verify successful workflow completion
        assert result['success'] is True
        assert result['zone_number'] == "2"
        assert result['num_violations'] == 3
        assert result['threshold'] == 5
        assert result['recommendation'] == 'safe'
        assert result['resolution'] == 1080
        assert result['display_success'] is True
        
        # Verify Frame service calls
        mock_frame_service.connect.assert_called_once()
        mock_frame_service.capture_image.assert_called_once_with(1080)
        mock_frame_service.display_text.assert_called()  # Called multiple times
        mock_frame_service.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_parking_check_connection_failure(self, checker, mock_frame_service):
        """Test workflow when Frame connection fails"""
        # Mock connection failure
        mock_frame_service.connect.return_value = {
            'success': False,
            'error': 'Bluetooth connection failed'
        }
        checker.frame_service = mock_frame_service
        
        result = await checker.run_parking_check()
        
        assert result['success'] is False
        assert result['step_failed'] == 'connection'
        assert 'Bluetooth connection failed' in result['error']
    
    @pytest.mark.asyncio
    async def test_run_parking_check_capture_failure(self, checker, mock_frame_service):
        """Test workflow when image capture fails"""
        # Mock capture failure
        mock_frame_service.capture_image.return_value = {
            'success': False,
            'error': 'Camera hardware error'
        }
        checker.frame_service = mock_frame_service
        
        result = await checker.run_parking_check()
        
        assert result['success'] is False
        assert result['step_failed'] == 'capture'
        assert 'Camera hardware error' in result['error']
        
        # Verify cleanup still happens
        mock_frame_service.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_parking_check_analysis_failure(self, checker, mock_frame_service):
        """Test workflow when zone analysis fails"""
        checker.frame_service = mock_frame_service
        
        # Mock analysis failure
        async def mock_extract_zone_failure(image_data):
            return False, None, "VLM processing error"
        
        checker.extract_zone_from_image = mock_extract_zone_failure
        
        result = await checker.run_parking_check()
        
        assert result['success'] is False
        assert result['step_failed'] == 'analysis'
        assert result['error'] == "VLM processing error"
        
        # Verify cleanup still happens
        mock_frame_service.disconnect.assert_called_once()


class TestParkingViolationsIntegration:
    """Integration tests for the complete parking violations system"""
    
    @pytest.mark.asyncio
    @patch('apps.parking_violations.requests.post')
    async def test_realistic_workflow_simulation(self, mock_post):
        """Simulate a realistic parking violations check workflow"""
        # Create checker instance
        checker = ParkingViolationsChecker(violation_threshold=6)
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'answer': 'I can see "Zone 5" written on the parking sign',
            'question': checker.zone_extraction_prompt,
            'timestamp': '2024-01-01T12:00:00',
            'processing_time_ms': 2100.0
        }
        mock_post.return_value = mock_response
        
        # Mock Frame service
        mock_frame_service = AsyncMock()
        mock_frame_service.connect.return_value = {'success': True}
        mock_frame_service.capture_image.return_value = {
            'success': True,
            'image_data': b'realistic_street_sign_image_data',
            'image_size_bytes': 2048,
            'resolution': 720
        }
        mock_frame_service.display_text.return_value = {'success': True}
        checker.frame_service = mock_frame_service
        
        # Run the workflow
        result = await checker.run_parking_check()
        
        # Verify results
        assert result['success'] is True
        assert result['zone_number'] == "5"
        assert result['num_violations'] == 15  # Zone 5 has high violations
        assert result['recommendation'] == 'risky'  # 15 > threshold of 6
        
        # Verify Frame glasses showed warning
        warning_calls = [call for call in mock_frame_service.display_text.call_args_list 
                        if 'fuhgedaboutit' in str(call)]
        assert len(warning_calls) > 0, "Should have displayed warning message"
    
    def test_zone_parsing_edge_cases(self):
        """Test zone parsing with various real-world VLM responses"""
        checker = ParkingViolationsChecker()
        
        # Test realistic VLM responses
        test_cases = [
            ("The parking sign shows 'Zone 3' clearly", "3"),
            ("I can see the number 12A on the street sign", "12A"),
            ("There is text reading 'AREA B' on the sign", "B"),
            ("The sign contains 'Section 7' in bold letters", "7"),
            ("I cannot make out any zone number in this image", None),
            ("The image is too blurry to read any text", None),
            ("NONE", None),
            ("42", "42"),
            ("Zone: 8 (Metered Parking)", "8"),
        ]
        
        for response, expected in test_cases:
            result = checker._parse_zone_from_response(response)
            assert result == expected, f"Failed for response: '{response}', expected: {expected}, got: {result}"


@pytest.mark.asyncio
async def test_main_function():
    """Test the main demo function runs without errors"""
    # This is more of a smoke test to ensure the main function structure is correct
    with patch('apps.parking_violations.ParkingViolationsChecker') as mock_checker_class:
        mock_checker = AsyncMock()
        mock_checker.run_parking_check.return_value = {
            'success': True,
            'zone_number': '3',
            'num_violations': 4,
            'threshold': 5,
            'recommendation': 'safe',
            'processing_time_seconds': 2.5,
            'image_size_bytes': 1024,
            'timestamp': '2024-01-01T12:00:00'
        }
        mock_checker_class.return_value = mock_checker
        
        # Import and run main (would normally be done via asyncio.run)
        from apps.parking_violations import main
        
        # This should complete without errors
        await main()
        
        # Verify the checker was created and used
        mock_checker_class.assert_called_once()
        mock_checker.run_parking_check.assert_called_once()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"]) 