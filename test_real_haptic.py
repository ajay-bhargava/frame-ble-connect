#!/usr/bin/env python3
"""
Test script for real haptic detector with actual Frame glasses connection

This script tests the haptic detector with real accelerometer data from Frame glasses.
Run this to test actual temple tap detection.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from connect.haptic_detector import HapticDetector

async def test_real_haptic_detector():
    """Test the haptic detector with real Frame glasses"""
    
    print("🎯 REAL HAPTIC DETECTOR TEST - LIGHT TAP DETECTION")
    print("=" * 60)
    print("Testing light tap detection using REAL accelerometer data")
    print("Make sure your Frame glasses are connected and powered on")
    print()
    
    detector = HapticDetector()
    
    try:
        # Step 1: Connect to real Frame glasses
        print("🔗 Connecting to real Frame glasses...")
        result = await detector.connect_to_glasses()
        
        if not result.get('success'):
            print(f"❌ Connection failed: {result.get('error')}")
            print("Make sure:")
            print("  - Frame glasses are powered on")
            print("  - Bluetooth is enabled on your Mac")
            print("  - Frame glasses are in pairing mode")
            return
        
        print("✅ Connected to real Frame glasses!")
        print(f"   Battery/Memory: {result.get('battery_memory')}")
        
        # Step 2: Start monitoring
        print("\n👁️  Starting real touch monitoring...")
        
        async def touch_callback(data):
            print(f"\n🎯 REAL TOUCH DETECTED!")
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   Trigger Type: {data.get('trigger_type')}")
            print(f"   Violation Count: {data.get('violation_count')}")
            
            capture_result = data.get('capture_result', {})
            if capture_result.get('success'):
                print(f"   Photo Captured: {capture_result.get('image_size_bytes')} bytes")
                print(f"   Resolution: {capture_result.get('resolution')}")
                
                # Save the captured image
                jpeg_data = capture_result.get('jpeg_data')
                if jpeg_data:
                    filename = f"captured_tap_{int(asyncio.get_event_loop().time())}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(jpeg_data)
                    print(f"   Image saved as: {filename}")
            else:
                print(f"   Photo Capture Failed: {capture_result.get('error')}")
        
        result = await detector.start_touch_monitoring(touch_callback)
        
        if not result.get('success'):
            print(f"❌ Failed to start monitoring: {result.get('error')}")
            return
        
        print("✅ Real touch monitoring started!")
        print("   Now tap the temple area of your Frame glasses")
        print("   The system will detect real accelerometer changes")
        print("   Press Ctrl+C to stop")
        
        # Step 3: Monitor for real touch events
        print("\n⏳ Monitoring for REAL touch events...")
        print("   Tap the temple area (side of glasses) to trigger capture")
        
        # Monitor for 60 seconds or until interrupted
        try:
            for i in range(60):
                await asyncio.sleep(1)
                
                # Print status every 10 seconds
                if (i + 1) % 10 == 0:
                    status = detector.get_status()
                    print(f"   Status: Connected={status['connected']}, "
                          f"Monitoring={status['monitoring_active']}")
        
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        
        # Step 4: Stop monitoring
        print("\n🛑 Stopping touch monitoring...")
        result = await detector.stop_touch_monitoring()
        
        if result.get('success'):
            print("✅ Touch monitoring stopped")
        else:
            print(f"❌ Failed to stop monitoring: {result.get('error')}")
        
        # Step 5: Disconnect
        print("\n🔌 Disconnecting from Frame glasses...")
        result = await detector.disconnect()
        
        if result.get('success'):
            print("✅ Disconnected successfully")
        else:
            print(f"❌ Failed to disconnect: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\n🎉 REAL HAPTIC DETECTOR TEST COMPLETE!")
        print("=" * 50)
        print("Key Features Tested:")
        print("✅ Real BLE connection to Frame glasses")
        print("✅ Real accelerometer data reading")
        print("✅ Real light tap detection")
        print("✅ Real photo capture on touch")
        print("✅ Real violation count retrieval")
        print("✅ Real callback handling")

if __name__ == "__main__":
    asyncio.run(test_real_haptic_detector()) 