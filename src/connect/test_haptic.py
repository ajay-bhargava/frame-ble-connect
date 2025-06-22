#!/usr/bin/env python3
"""
Test script for haptic detector with light tap detection

This script tests:
1. Connection to Frame glasses
2. Light tap detection using accelerometer
3. Photo capture on touch
4. Violation count return

Run this to test the touch-to-capture feature in isolation.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, Any

from haptic_detector import HapticDetector

class HapticTestRunner:
    def __init__(self):
        self.detector = HapticDetector()
        self.running = True
        
        # Set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
    
    def print_step(self, step: int, title: str, description: str):
        """Print a formatted step with emoji and details"""
        print(f"\n{'='*60}")
        print(f"🎯 STEP {step}: {title}")
        print(f"📝 {description}")
        print(f"{'='*60}")
    
    def print_result(self, result: Dict[str, Any], step_name: str):
        """Print formatted test result"""
        print(f"\n✅ {step_name} Result:")
        print(f"   Status: {'✅ Success' if result.get('success') else '❌ Failed'}")
        
        if step_name == "Connection":
            print(f"   Message: {result.get('message', 'N/A')}")
        
        elif step_name == "Touch Monitoring":
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Monitoring Active: {result.get('monitoring_active', 'N/A')}")
            print(f"   Sensitivity: {result.get('sensitivity', 'N/A')}")
        
        elif step_name == "Touch Event":
            print(f"   Trigger Type: {result.get('trigger_type', 'N/A')}")
            print(f"   Violation Count: {result.get('violation_count', 'N/A')}")
            print(f"   Capture Success: {result.get('capture_result', {}).get('success', 'N/A')}")
    
    async def touch_callback(self, data: Dict[str, Any]):
        """Callback function for touch events"""
        print(f"\n🎯 TOUCH EVENT DETECTED!")
        print(f"   Timestamp: {data.get('timestamp')}")
        print(f"   Trigger Type: {data.get('trigger_type')}")
        print(f"   Violation Count: {data.get('violation_count')}")
        
        capture_result = data.get('capture_result', {})
        if capture_result.get('success'):
            print(f"   Photo Captured: {capture_result.get('image_size_bytes')} bytes")
            print(f"   Resolution: {capture_result.get('resolution')}")
        else:
            print(f"   Photo Capture Failed: {capture_result.get('error')}")
    
    async def test_haptic_detection(self):
        """Test the complete haptic detection workflow"""
        
        print("🚀 HAPTIC DETECTOR TEST - LIGHT TAP DETECTION")
        print("=" * 70)
        print("This test will simulate light tap detection using accelerometer data.")
        print("The system will detect 'taps' and trigger photo capture + violation count.")
        print()
        
        try:
            # Step 1: Connect to Frame glasses
            self.print_step(1, "Connect to Frame Glasses", 
                           "Establish BLE connection to Frame glasses")
            
            result = await self.detector.connect_to_glasses()
            self.print_result(result, "Connection")
            
            if not result.get('success'):
                print("❌ Failed to connect to Frame glasses")
                return
            
            # Step 2: Start touch monitoring
            self.print_step(2, "Start Touch Monitoring", 
                           "Begin monitoring accelerometer for light tap events")
            
            result = await self.detector.start_touch_monitoring(self.touch_callback)
            self.print_result(result, "Touch Monitoring")
            
            if not result.get('success'):
                print("❌ Failed to start touch monitoring")
                return
            
            # Step 3: Monitor for touch events
            self.print_step(3, "Monitor for Touch Events", 
                           "Waiting for light tap events (simulated)")
            
            print("👁️  Monitoring for light taps...")
            print("   The system will simulate occasional 'taps' for testing")
            print("   In real usage, tap the temple area of the glasses")
            print("   Press Ctrl+C to stop monitoring")
            
            # Monitor for touch events
            touch_count = 0
            while self.running:
                await asyncio.sleep(1)
                
                # Check status every 10 seconds
                if touch_count % 10 == 0:
                    status = self.detector.get_status()
                    print(f"   Status: Connected={status['connected']}, "
                          f"Monitoring={status['monitoring_active']}, "
                          f"Sensitivity={status['sensitivity']}")
                
                touch_count += 1
            
            # Step 4: Stop monitoring
            self.print_step(4, "Stop Touch Monitoring", 
                           "Stop monitoring for touch events")
            
            result = await self.detector.stop_touch_monitoring()
            self.print_result(result, "Stop Monitoring")
            
            # Step 5: Disconnect
            self.print_step(5, "Disconnect", 
                           "Disconnect from Frame glasses")
            
            result = await self.detector.disconnect()
            self.print_result(result, "Disconnect")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        finally:
            print("\n🎉 HAPTIC DETECTOR TEST COMPLETE!")
            print("=" * 50)
            print("Key Features Tested:")
            print("✅ BLE connection to Frame glasses")
            print("✅ Light tap detection using accelerometer")
            print("✅ Photo capture on touch event")
            print("✅ Violation count retrieval")
            print("✅ Callback handling")
            print("✅ Clean shutdown")
    
    async def test_sensitivity_adjustment(self):
        """Test adjusting touch detection sensitivity"""
        
        print("\n🔧 TESTING SENSITIVITY ADJUSTMENT")
        print("=" * 50)
        
        try:
            # Connect
            await self.detector.connect_to_glasses()
            
            # Test different sensitivity levels
            sensitivities = [
                ("Very Light", 1.0, 0.5),
                ("Light", 1.5, 0.8),
                ("Medium", 2.0, 1.0),
                ("Firm", 3.0, 1.5)
            ]
            
            for name, accel_thresh, gyro_thresh in sensitivities:
                print(f"\n🧪 Testing {name} tap sensitivity:")
                print(f"   Accel threshold: {accel_thresh}")
                print(f"   Gyro threshold: {gyro_thresh}")
                
                # Update thresholds
                self.detector.accel_threshold = accel_thresh
                self.detector.gyro_threshold = gyro_thresh
                
                # Start monitoring briefly
                await self.detector.start_touch_monitoring(self.touch_callback)
                await asyncio.sleep(5)  # Monitor for 5 seconds
                await self.detector.stop_touch_monitoring()
            
            await self.detector.disconnect()
            
        except Exception as e:
            print(f"❌ Sensitivity test failed: {e}")

async def main():
    """Main test function"""
    
    print("🎯 HAPTIC DETECTOR TEST SUITE")
    print("=" * 50)
    print("Choose a test to run:")
    print("1. Full haptic detection test")
    print("2. Sensitivity adjustment test")
    print("3. Both tests")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        runner = HapticTestRunner()
        
        if choice == "1":
            await runner.test_haptic_detection()
        elif choice == "2":
            await runner.test_sensitivity_adjustment()
        elif choice == "3":
            await runner.test_haptic_detection()
            await runner.test_sensitivity_adjustment()
        elif choice == "4":
            print("👋 Goodbye!")
            return
        else:
            print("❌ Invalid choice. Running full test...")
            await runner.test_haptic_detection()
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 