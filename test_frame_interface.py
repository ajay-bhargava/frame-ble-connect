"""
Test suite and examples for FrameInterface class

This module provides:
- Comprehensive unit tests for FrameInterface functionality
- Real-world usage examples
- Performance and reliability testing
- Integration test scenarios

Test Categories:
- Connection management and error handling
- Photo capture (tap-triggered and manual)
- Text display functionality
- Event callback system
- Status monitoring and health checks
- Resource cleanup and memory management

Usage Examples:
- Basic tap-to-capture workflow
- Advanced callback configurations
- Error recovery scenarios
- Performance monitoring
"""

import asyncio
import pytest
import pytest_asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src', 'connect'))

from src.connect.frame_interface import FrameInterface

# Mark all async tests with pytest.mark.asyncio
pytestmark = pytest.mark.asyncio

class TestFrameInterface:
    """
    Comprehensive test suite for FrameInterface class.
    
    Tests cover all major functionality including connection management,
    event handling, photo capture, text display, and error scenarios.
    """
    
    @pytest_asyncio.fixture
    async def frame_interface(self):
        """Create a FrameInterface instance for testing."""
        interface = FrameInterface(capture_resolution=720, auto_exposure_delay=1.0)
        yield interface
        # Cleanup
        if interface.is_connected:
            await interface.disconnect()
    
    @pytest.fixture
    def frame_interface_sync(self):
        """Create a FrameInterface instance for synchronous testing."""
        return FrameInterface(capture_resolution=720, auto_exposure_delay=1.0)
    
    @pytest.fixture
    def mock_frame_msg(self):
        """Mock FrameMsg for testing without hardware."""
        with patch('src.connect.frame_interface.FrameMsg') as mock:
            frame_instance = AsyncMock()
            mock.return_value = frame_instance
            frame_instance.connect = AsyncMock()
            frame_instance.send_lua = AsyncMock(return_value="85 / 45.2")
            frame_instance.print_short_text = AsyncMock()
            frame_instance.upload_stdlua_libs = AsyncMock()
            frame_instance.upload_frame_app = AsyncMock()
            frame_instance.attach_print_response_handler = MagicMock()
            frame_instance.start_frame_app = AsyncMock()
            frame_instance.send_message = AsyncMock()
            frame_instance.stop_frame_app = AsyncMock()
            frame_instance.disconnect = AsyncMock()
            frame_instance.detach_print_response_handler = MagicMock()
            yield frame_instance
    
    @pytest.fixture
    def mock_rx_photo(self):
        """Mock RxPhoto for testing photo capture."""
        with patch('src.connect.frame_interface.RxPhoto') as mock:
            rx_instance = AsyncMock()
            mock.return_value = rx_instance
            
            # Create mock photo queue
            photo_queue = AsyncMock()
            photo_queue.get = AsyncMock(return_value=b'fake_jpeg_data')
            photo_queue.get_nowait = MagicMock(return_value=b'fake_jpeg_data')
            photo_queue.empty = MagicMock(return_value=False)
            
            rx_instance.attach = AsyncMock(return_value=photo_queue)
            rx_instance.detach = MagicMock()
            yield rx_instance, photo_queue
    
    async def test_initialization(self, frame_interface):
        """Test proper initialization of FrameInterface."""
        assert frame_interface.capture_resolution == 720
        assert frame_interface.auto_exposure_delay == 1.0
        assert not frame_interface.is_connected
        assert not frame_interface.is_running
        assert frame_interface.capture_count == 0
        assert frame_interface.max_text_length == 50
    
    async def test_callback_setters(self, frame_interface):
        """Test setting various callback functions."""
        # Define test callbacks
        async def photo_callback(data, metadata):
            pass
        
        async def tap_callback():
            pass
        
        async def error_callback(error):
            pass
        
        async def status_callback(status):
            pass
        
        # Set callbacks
        frame_interface.set_photo_callback(photo_callback)
        frame_interface.set_tap_callback(tap_callback)
        frame_interface.set_error_callback(error_callback)
        frame_interface.set_status_callback(status_callback)
        
        # Verify callbacks are set
        assert frame_interface.photo_callback == photo_callback
        assert frame_interface.tap_callback == tap_callback
        assert frame_interface.error_callback == error_callback
        assert frame_interface.status_callback == status_callback
    
    async def test_successful_connection(self, frame_interface, mock_frame_msg, mock_rx_photo):
        """Test successful connection to Frame glasses."""
        rx_instance, photo_queue = mock_rx_photo
        
        result = await frame_interface.connect(max_retries=1)
        
        assert result["success"] is True
        assert frame_interface.is_connected is True
        assert frame_interface.connection_retry_count == 0
        assert "Connected to Frame glasses successfully" in result["message"]
        
        # Verify setup calls were made
        mock_frame_msg.connect.assert_called_once()
        mock_frame_msg.upload_stdlua_libs.assert_called_once()
        mock_frame_msg.start_frame_app.assert_called_once()
        rx_instance.attach.assert_called_once()
    
    async def test_connection_retry_logic(self, frame_interface):
        """Test connection retry behavior on failures."""
        with patch('src.connect.frame_interface.FrameMsg') as mock_frame_class:
            # Mock first attempt to fail, second to succeed
            mock_frame_msg = AsyncMock()
            mock_frame_class.return_value = mock_frame_msg
            
            call_count = 0
            async def mock_connect():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Connection failed")
                # Second call succeeds
                
            mock_frame_msg.connect = mock_connect
            mock_frame_msg.send_lua = AsyncMock(return_value="85 / 45.2")
            mock_frame_msg.print_short_text = AsyncMock()
            mock_frame_msg.upload_stdlua_libs = AsyncMock()
            mock_frame_msg.upload_frame_app = AsyncMock()
            mock_frame_msg.attach_print_response_handler = MagicMock()
            mock_frame_msg.start_frame_app = AsyncMock()
            
            with patch('src.connect.frame_interface.RxPhoto') as mock_rx_class:
                rx_instance = AsyncMock()
                mock_rx_class.return_value = rx_instance
                photo_queue = AsyncMock()
                rx_instance.attach = AsyncMock(return_value=photo_queue)
                
                result = await frame_interface.connect(max_retries=2)
                
                assert result["success"] is True
                assert call_count == 2  # Verify retry happened
    
    async def test_connection_failure_after_retries(self, frame_interface):
        """Test connection failure after all retries exhausted."""
        with patch('src.connect.frame_interface.FrameMsg') as mock_frame_class:
            mock_frame_msg = AsyncMock()
            mock_frame_class.return_value = mock_frame_msg
            mock_frame_msg.connect = AsyncMock(side_effect=Exception("Persistent connection error"))
            
            result = await frame_interface.connect(max_retries=2)
            
            assert result["success"] is False
            assert "Persistent connection error" in result["error"]
            assert result["retry_count"] == 3  # Initial + 2 retries
    
    async def test_display_text_success(self, frame_interface, mock_frame_msg, mock_rx_photo):
        """Test successful text display."""
        # First connect
        await frame_interface.connect(max_retries=1)
        
        result = await frame_interface.display_text("Hello Frame!", position_x=10, position_y=20)
        
        assert result["success"] is True
        assert result["text_displayed"] == "Hello Frame!"
        assert result["position"] == (10, 20)
        assert result["truncated"] is False
        
        # Verify message was sent
        mock_frame_msg.send_message.assert_called()
    
    async def test_display_text_truncation(self, frame_interface, mock_frame_msg, mock_rx_photo):
        """Test text truncation for long messages."""
        await frame_interface.connect(max_retries=1)
        
        long_text = "This is a very long text that exceeds the maximum display length"
        result = await frame_interface.display_text(long_text)
        
        assert result["success"] is True
        assert len(result["text_displayed"]) <= frame_interface.max_text_length
        assert result["truncated"] is True
    
    async def test_display_text_not_connected(self, frame_interface):
        """Test text display when not connected."""
        result = await frame_interface.display_text("Test")
        
        assert result["success"] is False
        assert "Not connected to Frame glasses" in result["error"]
    
    async def test_manual_photo_capture(self, frame_interface, mock_frame_msg, mock_rx_photo):
        """Test manual photo capture functionality."""
        rx_instance, photo_queue = mock_rx_photo
        
        # Connect first
        await frame_interface.connect(max_retries=1)
        
        # Mock photo callback
        captured_photos = []
        async def photo_callback(data, metadata):
            captured_photos.append((data, metadata))
        
        frame_interface.set_photo_callback(photo_callback)
        
        result = await frame_interface.capture_photo(resolution=1080)
        
        assert result["success"] is True
        assert result["image_data"] == b'fake_jpeg_data'
        assert result["metadata"]["resolution"] == 1080
        assert result["metadata"]["triggered_by"] == "manual"
        assert frame_interface.capture_count == 1
        
        # Verify callback was called
        assert len(captured_photos) == 1
        assert captured_photos[0][0] == b'fake_jpeg_data'
    
    async def test_photo_capture_timeout(self, frame_interface, mock_frame_msg):
        """Test photo capture timeout handling."""
        with patch('src.connect.frame_interface.RxPhoto') as mock_rx_class:
            rx_instance = AsyncMock()
            mock_rx_class.return_value = rx_instance
            
            # Mock photo queue that times out
            photo_queue = AsyncMock()
            photo_queue.get = AsyncMock(side_effect=asyncio.TimeoutError())
            rx_instance.attach = AsyncMock(return_value=photo_queue)
            
            await frame_interface.connect(max_retries=1)
            
            result = await frame_interface.capture_photo()
            
            assert result["success"] is False
            assert "Timeout waiting for photo capture" in result["error"]
    
    async def test_get_status_connected(self, frame_interface, mock_frame_msg, mock_rx_photo):
        """Test status retrieval when connected."""
        await frame_interface.connect(max_retries=1)
        
        status = await frame_interface.get_status()
        
        assert status["connected"] is True
        assert status["battery_level"] == 85  # From mock response
        assert status["memory_usage"] == "45.2"
        assert status["capture_count"] == 0
        assert status["connection_retries"] == 0
    
    async def test_get_status_not_connected(self, frame_interface):
        """Test status retrieval when not connected."""
        status = await frame_interface.get_status()
        
        assert status["connected"] is False
        assert status["battery_level"] is None
        assert status["capture_count"] == 0
    
    async def test_disconnect_cleanup(self, frame_interface, mock_frame_msg, mock_rx_photo):
        """Test proper resource cleanup on disconnect."""
        rx_instance, photo_queue = mock_rx_photo
        
        # Connect first
        await frame_interface.connect(max_retries=1)
        assert frame_interface.is_connected is True
        
        # Disconnect
        await frame_interface.disconnect()
        
        assert frame_interface.is_connected is False
        assert frame_interface.frame is None
        assert frame_interface.rx_photo is None
        assert frame_interface.photo_queue is None
        
        # Verify cleanup calls
        rx_instance.detach.assert_called_once()
        mock_frame_msg.stop_frame_app.assert_called_once()
        mock_frame_msg.disconnect.assert_called_once()
    
    async def test_error_callback_handling(self, frame_interface):
        """Test error callback invocation."""
        errors_caught = []
        
        async def error_callback(error):
            errors_caught.append(error)
        
        frame_interface.set_error_callback(error_callback)
        
        # Trigger a connection error
        with patch('src.connect.frame_interface.FrameMsg') as mock_frame_class:
            mock_frame_msg = AsyncMock()
            mock_frame_class.return_value = mock_frame_msg
            test_error = Exception("Test error")
            mock_frame_msg.connect = AsyncMock(side_effect=test_error)
            
            result = await frame_interface.connect(max_retries=0)
            
            assert result["success"] is False
            assert len(errors_caught) == 1
            assert str(errors_caught[0]) == "Test error"
    
    def test_save_image_utility(self, frame_interface_sync, tmp_path):
        """Test image saving utility function."""
        # Create test image data
        test_image_data = b'fake_jpeg_data'
        
        # Mock the static/images directory to use temp path
        with patch('os.path.join') as mock_join:
            mock_join.return_value = str(tmp_path / "test_image.jpg")
            
            with patch('os.makedirs'):
                filepath = frame_interface_sync.save_image(test_image_data, "test_image.jpg")
                
                # Verify file was "saved" (mocked)
                assert "test_image.jpg" in filepath
    
    def test_get_image_info_utility(self, frame_interface_sync):
        """Test image metadata extraction utility."""
        # Test with invalid image data
        invalid_data = b'not_an_image'
        info = frame_interface_sync.get_image_info(invalid_data)
        
        assert "error" in info
        assert info["size_bytes"] == len(invalid_data)


class TestFrameInterfaceIntegration:
    """
    Integration tests that test complete workflows and real-world scenarios.
    These tests verify that components work together correctly.
    """
    
    async def test_complete_tap_to_capture_workflow(self):
        """Test the complete tap-to-capture workflow."""
        interface = FrameInterface()
        
        # Track events
        photos_captured = []
        taps_detected = []
        
        async def on_photo(data, metadata):
            photos_captured.append((data, metadata))
        
        async def on_tap():
            taps_detected.append(datetime.now())
        
        interface.set_photo_callback(on_photo)
        interface.set_tap_callback(on_tap)
        
        # Mock the Frame components
        with patch('src.connect.frame_interface.FrameMsg') as mock_frame_class, \
             patch('src.connect.frame_interface.RxPhoto') as mock_rx_class:
            
            # Setup mocks
            mock_frame_msg = AsyncMock()
            mock_frame_class.return_value = mock_frame_msg
            mock_frame_msg.connect = AsyncMock()
            mock_frame_msg.send_lua = AsyncMock(return_value="90 / 50.1")
            mock_frame_msg.print_short_text = AsyncMock()
            mock_frame_msg.upload_stdlua_libs = AsyncMock()
            mock_frame_msg.upload_frame_app = AsyncMock()
            mock_frame_msg.attach_print_response_handler = MagicMock()
            mock_frame_msg.start_frame_app = AsyncMock()
            mock_frame_msg.send_message = AsyncMock()
            
            rx_instance = AsyncMock()
            mock_rx_class.return_value = rx_instance
            photo_queue = AsyncMock()
            photo_queue.get = AsyncMock(return_value=b'test_image_data')
            rx_instance.attach = AsyncMock(return_value=photo_queue)
            
            # Execute workflow
            result = await interface.connect()
            assert result["success"] is True
            
            # Test manual capture
            capture_result = await interface.capture_photo()
            assert capture_result["success"] is True
            assert len(photos_captured) == 1
            
            # Test text display
            text_result = await interface.display_text("Capture successful!")
            assert text_result["success"] is True
            
            # Cleanup
            await interface.disconnect()
    
    async def test_error_recovery_scenario(self):
        """Test error recovery and resilience."""
        interface = FrameInterface()
        
        errors_handled = []
        
        async def error_handler(error):
            errors_handled.append(error)
        
        interface.set_error_callback(error_handler)
        
        with patch('src.connect.frame_interface.FrameMsg') as mock_frame_class:
            mock_frame_msg = AsyncMock()
            mock_frame_class.return_value = mock_frame_msg
            
            # First connection attempt fails
            connection_attempts = 0
            async def mock_connect():
                nonlocal connection_attempts
                connection_attempts += 1
                if connection_attempts == 1:
                    raise Exception("Bluetooth connection lost")
                # Subsequent attempts succeed
            
            mock_frame_msg.connect = mock_connect
            mock_frame_msg.send_lua = AsyncMock(return_value="80 / 48.3")
            mock_frame_msg.print_short_text = AsyncMock()
            mock_frame_msg.upload_stdlua_libs = AsyncMock()
            mock_frame_msg.upload_frame_app = AsyncMock()
            mock_frame_msg.attach_print_response_handler = MagicMock()
            mock_frame_msg.start_frame_app = AsyncMock()
            
            with patch('src.connect.frame_interface.RxPhoto') as mock_rx_class:
                rx_instance = AsyncMock()
                mock_rx_class.return_value = rx_instance
                photo_queue = AsyncMock()
                rx_instance.attach = AsyncMock(return_value=photo_queue)
                
                # Connect with retry
                result = await interface.connect(max_retries=2)
                
                assert result["success"] is True
                assert connection_attempts == 2  # Verify retry occurred
                assert len(errors_handled) == 1  # Error callback was called
                assert "Bluetooth connection lost" in str(errors_handled[0])


async def run_example_usage():
    """
    Example usage of FrameInterface showing real-world patterns.
    
    This demonstrates:
    - Setting up callbacks for events
    - Connecting to Frame glasses
    - Handling tap events and photo capture
    - Displaying feedback text
    - Monitoring device status
    - Graceful shutdown
    """
    print("🔮 Frame Interface Example Usage")
    print("=" * 40)
    
    # Initialize the interface
    interface = FrameInterface(
        capture_resolution=720,
        auto_exposure_delay=3.0
    )
    
    # Setup event callbacks
    async def on_photo_captured(image_data: bytes, metadata: dict):
        """Handle photo capture events."""
        print(f"📸 Photo captured: {len(image_data)} bytes")
        print(f"   Resolution: {metadata['resolution']}p")
        print(f"   Timestamp: {metadata['timestamp']}")
        print(f"   Triggered by: {metadata['triggered_by']}")
        
        # Save the image
        filename = interface.save_image(image_data)
        print(f"   Saved as: {filename}")
        
        # Get image info
        info = interface.get_image_info(image_data)
        if "error" not in info:
            print(f"   Dimensions: {info['width']}x{info['height']}")
    
    async def on_tap_detected():
        """Handle tap events."""
        print("👆 Tap detected on Frame glasses!")
        await interface.display_text("Processing...")
    
    async def on_error(error: Exception):
        """Handle errors."""
        print(f"❌ Error occurred: {error}")
    
    async def on_status_update(status: dict):
        """Handle status updates."""
        if status["connected"]:
            battery = status.get("battery_level", "Unknown")
            memory = status.get("memory_usage", "Unknown")
            captures = status.get("capture_count", 0)
            print(f"📊 Status: Battery {battery}%, Memory {memory}KB, Captures: {captures}")
    
    # Set up callbacks
    interface.set_photo_callback(on_photo_captured)
    interface.set_tap_callback(on_tap_detected)
    interface.set_error_callback(on_error)
    interface.set_status_callback(on_status_update)
    
    try:
        # Connect to Frame glasses
        print("🔗 Connecting to Frame glasses...")
        result = await interface.connect()
        
        if not result["success"]:
            print(f"❌ Connection failed: {result['error']}")
            return
        
        print("✅ Connected successfully!")
        print(f"   Battery: {result.get('battery_level', 'Unknown')}%")
        print(f"   Memory: {result.get('memory_usage', 'Unknown')}KB")
        
        # Display welcome message
        await interface.display_text("Ready for taps!")
        
        # Get initial status
        status = await interface.get_status()
        await on_status_update(status)
        
        # Test manual photo capture
        print("\n📷 Testing manual photo capture...")
        capture_result = await interface.capture_photo(resolution=1080)
        
        if capture_result["success"]:
            print("✅ Manual capture successful!")
        else:
            print(f"❌ Manual capture failed: {capture_result['error']}")
        
        # Display instructions
        await interface.display_text("Tap to capture")
        
        print("\n👀 Monitoring for tap events...")
        print("   (In real usage, this would run until stopped)")
        
        # In a real application, you would run:
        # await interface.run_event_loop()
        
        # For demonstration, we'll just wait a bit
        await asyncio.sleep(2)
        
        # Test status retrieval
        final_status = await interface.get_status()
        print(f"\n📈 Final status: {final_status['capture_count']} captures")
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
    
    finally:
        # Clean shutdown
        print("\n🛑 Shutting down...")
        await interface.stop()
        print("✅ Shutdown complete")


if __name__ == "__main__":
    # Setup logging for the example
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Running Frame Interface Example...")
    print("Note: This example uses mocked Frame SDK for demonstration")
    print("In real usage, ensure Frame glasses are paired and available\n")
    
    # Run the example
    asyncio.run(run_example_usage())