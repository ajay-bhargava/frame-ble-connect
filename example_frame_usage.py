#!/usr/bin/env python3
"""
Enhanced Frame Interface Usage Example

This example demonstrates the improved Frame interface capabilities including:
- Robust photo capture processing
- Enhanced tap detection
- Improved error handling
- Better status monitoring
- Comprehensive callback usage

Run this to test the Frame interface improvements with real or simulated hardware.
"""

import asyncio
import logging
import json
from datetime import datetime
from src.connect.frame_interface import FrameInterface


async def enhanced_frame_example():
    """
    Comprehensive example showcasing all Frame interface improvements.
    
    This example demonstrates:
    1. Enhanced connection with validation
    2. Multiple callback types with robust error handling
    3. Improved photo processing with metadata
    4. Real-time status monitoring
    5. Graceful shutdown and cleanup
    """
    
    # Initialize Frame interface with enhanced settings
    interface = FrameInterface(
        capture_resolution=720,
        auto_exposure_delay=2.0  # Balanced for quick startup but good quality
    )
    
    # Statistics tracking
    photos_captured = []
    taps_detected = []
    errors_encountered = []
    status_updates = []
    
    # Enhanced photo callback with comprehensive metadata handling
    async def on_photo_captured(image_data: bytes, metadata: dict):
        """Handle captured photos with enhanced processing."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n📸 [{timestamp}] Photo captured!")
        print(f"   Size: {len(image_data):,} bytes")
        print(f"   Resolution: {metadata.get('resolution', 'unknown')}p")
        print(f"   Triggered by: {metadata.get('triggered_by', 'unknown')}")
        print(f"   Capture count: {metadata.get('capture_count', 0)}")
        
        # Save photo with enhanced filename
        try:
            trigger_type = metadata.get('triggered_by', 'unknown')
            capture_num = metadata.get('capture_count', 0)
            filename = f"enhanced_capture_{trigger_type}_{capture_num}.jpg"
            filepath = interface.save_image(image_data, filename)
            print(f"   Saved to: {filepath}")
            
            # Get enhanced image info
            image_info = interface.get_image_info(image_data)
            if 'error' not in image_info:
                print(f"   Dimensions: {image_info['width']}x{image_info['height']}")
                print(f"   Format: {image_info['format']}")
            
            photos_captured.append({
                'timestamp': metadata['timestamp'],
                'size': len(image_data),
                'filepath': filepath,
                'metadata': metadata
            })
            
        except Exception as e:
            print(f"   ⚠️ Error saving photo: {e}")
    
    # Enhanced tap callback with timing
    async def on_tap_detected():
        """Handle tap events with enhanced feedback."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        tap_count = len(taps_detected) + 1
        print(f"\n👆 [{timestamp}] Tap #{tap_count} detected!")
        
        # Provide immediate feedback to user
        await interface.display_text(f"Tap #{tap_count} - Capturing...")
        
        taps_detected.append({
            'timestamp': timestamp,
            'tap_number': tap_count
        })
    
    # Enhanced error callback with categorization
    async def on_error(error: Exception):
        """Handle errors with enhanced logging and recovery."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_type = type(error).__name__
        print(f"\n❌ [{timestamp}] Error ({error_type}): {str(error)}")
        
        errors_encountered.append({
            'timestamp': timestamp,
            'type': error_type,
            'message': str(error)
        })
        
        # Attempt automatic recovery for certain error types
        if "connection" in str(error).lower():
            print("   🔄 Attempting automatic reconnection...")
            # The interface will handle reconnection automatically
    
    # Enhanced status callback with detailed monitoring
    async def on_status_update(status: dict):
        """Handle status updates with enhanced monitoring."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        battery = status.get('battery_level', 'unknown')
        memory = status.get('memory_usage', 'unknown')
        captures = status.get('capture_count', 0)
        
        print(f"\n📊 [{timestamp}] Status Update:")
        print(f"   Battery: {battery}%")
        print(f"   Memory: {memory} KB")
        print(f"   Photos: {captures}")
        print(f"   Connected: {status.get('connected', False)}")
        
        status_updates.append({
            'timestamp': timestamp,
            'status': status.copy()
        })
    
    # Register all enhanced callbacks
    interface.set_photo_callback(on_photo_captured)
    interface.set_tap_callback(on_tap_detected)
    interface.set_error_callback(on_error)
    interface.set_status_callback(on_status_update)
    
    try:
        print("🚀 Starting Enhanced Frame Interface Example")
        print("="*60)
        
        # Enhanced connection with detailed feedback
        print("🔗 Connecting to Frame glasses...")
        connection_result = await interface.connect(max_retries=3)
        
        if not connection_result["success"]:
            print(f"❌ Connection failed: {connection_result['error']}")
            return
        
        print("✅ Connected successfully!")
        print(f"   Battery: {connection_result.get('battery_level', 'unknown')}%")
        print(f"   Connection time: {connection_result.get('connection_time', 'unknown')}")
        
        # Enhanced text display sequence
        print("\n📝 Testing enhanced text display...")
        
        # Test basic display
        result1 = await interface.display_text("Frame Enhanced!")
        if result1["success"]:
            print(f"✅ Text displayed: '{result1['text_displayed']}'")
        
        await asyncio.sleep(2)
        
        # Test positioning
        result2 = await interface.display_text("Ready for taps", position_x=1, position_y=50)
        if result2["success"]:
            print(f"✅ Positioned text: '{result2['text_displayed']}' at {result2['position']}")
        
        # Test manual capture
        print("\n📷 Testing manual photo capture...")
        capture_result = await interface.capture_photo()
        if capture_result["success"]:
            print("✅ Manual capture successful!")
        else:
            print(f"❌ Manual capture failed: {capture_result['error']}")
        
        # Enhanced event loop with monitoring
        print("\n🔄 Starting enhanced event loop...")
        print("👆 Tap your Frame glasses to trigger photo capture!")
        print("📊 Status updates every 30 seconds")
        print("⏹️  Press Ctrl+C to stop gracefully")
        
        # Run enhanced event loop with faster status updates for demo
        await interface.run_event_loop(status_update_interval=30.0)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping gracefully...")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        
    finally:
        # Enhanced cleanup with statistics
        print("\n🛑 Shutting down...")
        await interface.stop()
        
        # Display enhanced session statistics
        print("\n📈 Session Statistics:")
        print("="*40)
        print(f"Photos captured: {len(photos_captured)}")
        print(f"Taps detected: {len(taps_detected)}")
        print(f"Errors encountered: {len(errors_encountered)}")
        print(f"Status updates: {len(status_updates)}")
        
        if photos_captured:
            total_size = sum(photo['size'] for photo in photos_captured)
            print(f"Total image data: {total_size:,} bytes")
            print("Recent captures:")
            for photo in photos_captured[-3:]:  # Show last 3
                print(f"  - {photo['filepath']} ({photo['size']:,} bytes)")
        
        if errors_encountered:
            print("Errors encountered:")
            for error in errors_encountered:
                print(f"  - {error['timestamp']}: {error['type']} - {error['message']}")
        
        print("\n✅ Enhanced Frame interface example completed!")


if __name__ == "__main__":
    # Enhanced logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('frame_interface_enhanced.log')
        ]
    )
    
    print("Enhanced Frame Interface Example")
    print("This example demonstrates all the improvements made to the Frame interface")
    print("Including enhanced photo processing, tap detection, and error handling\n")
    
    # Run the enhanced example
    asyncio.run(enhanced_frame_example()) 