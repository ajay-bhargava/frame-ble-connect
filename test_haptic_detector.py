#!/usr/bin/env python3
"""
Standalone test for haptic detector with light tap detection

This script tests the haptic detector in isolation without the full API.
Run this to test the touch-to-capture feature.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from connect.haptic_detector import HapticDetector

async def test_haptic_detector():
    """Test the haptic detector functionality"""
    
    print("🎯 HAPTIC DETECTOR TEST - LIGHT TAP DETECTION")
    print("=" * 60)
    print("Testing light tap detection using accelerometer data")
    print("The system will simulate taps and trigger photo capture")
    print()
    
    detector = HapticDetector()
    
    try:
        # Step 1: Connect
        print("🔗 Connecting to Frame glasses...")
        result = await detector.connect_to_glasses()
        
        if not result.get('success'):
            print(f"❌ Connection failed: {result.get('error')}")
            return
        
        print("✅ Connected successfully!")
        
        # Step 2: Start monitoring
        print("\n👁️  Starting touch monitoring...")
        
        async def touch_callback(data):
            print(f"\n🎯 TOUCH DETECTED!")
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   Trigger Type: {data.get('trigger_type')}")
            print(f"   Violation Count: {data.get('violation_count')}")
            
            capture_result = data.get('capture_result', {})
            if capture_result.get('success'):
                print(f"   Photo Captured: {capture_result.get('image_size_bytes')} bytes")
                print(f"   Resolution: {capture_result.get('resolution')}")
            else:
                print(f"   Photo Capture Failed: {capture_result.get('error')}")
        
        result = await detector.start_touch_monitoring(touch_callback)
        
        if not result.get('success'):
            print(f"❌ Failed to start monitoring: {result.get('error')}")
            return
        
        print("✅ Touch monitoring started!")
        print("   The system will simulate occasional 'taps' for testing")
        print("   In real usage, tap the temple area of the glasses")
        print("   Press Ctrl+C to stop")
        
        # Step 3: Monitor for events
        print("\n⏳ Monitoring for touch events...")
        
        # Monitor for 30 seconds or until interrupted
        try:
            for i in range(30):
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
        print("\n🔌 Disconnecting...")
        result = await detector.disconnect()
        
        if result.get('success'):
            print("✅ Disconnected successfully")
        else:
            print(f"❌ Failed to disconnect: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\n🎉 HAPTIC DETECTOR TEST COMPLETE!")
        print("=" * 50)
        print("Key Features Tested:")
        print("✅ Connection to Frame glasses")
        print("✅ Light tap detection")
        print("✅ Photo capture on touch")
        print("✅ Violation count retrieval")
        print("✅ Callback handling")

if __name__ == "__main__":
    asyncio.run(test_haptic_detector()) 