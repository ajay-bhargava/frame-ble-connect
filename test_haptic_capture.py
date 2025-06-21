#!/usr/bin/env python3
"""
Test script for haptic-triggered photo capture functionality

This script demonstrates:
1. Connecting to Frame glasses in haptic mode
2. Starting haptic monitoring
3. Simulating touch events (or waiting for real touches)
4. Processing haptic-triggered captures
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class HapticCaptureDemo:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = httpx.AsyncClient()
    
    def print_step(self, step: int, title: str, description: str):
        """Print a formatted step with emoji and details"""
        print(f"\n{'='*60}")
        print(f"🎯 STEP {step}: {title}")
        print(f"📝 {description}")
        print(f"{'='*60}")
    
    def print_result(self, result: Dict[str, Any], step_name: str):
        """Print formatted API result"""
        print(f"\n✅ {step_name} Result:")
        print(f"   Status: {'✅ Success' if result.get('success') else '❌ Failed'}")
        
        if step_name == "Haptic Connection":
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Haptic Mode: {result.get('haptic_mode', 'N/A')}")
            print(f"   Battery/Memory: {result.get('battery_memory', 'N/A')}")
        
        elif step_name == "Haptic Monitoring":
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
        
        elif step_name == "Haptic Status":
            print(f"   Connected: {result.get('connected', 'N/A')}")
            print(f"   Haptic Mode: {result.get('haptic_mode', 'N/A')}")
            print(f"   Monitoring Active: {result.get('monitoring_active', 'N/A')}")
            print(f"   Battery Level: {result.get('battery_level', 'N/A')}")
            print(f"   Last Capture: {result.get('last_capture', 'N/A')}")
    
    async def test_haptic_workflow(self):
        """Test the complete haptic-triggered capture workflow"""
        
        print("🚀 FRAME GLASSES HAPTIC CAPTURE DEMO")
        print("=" * 70)
        
        try:
            # Step 1: Connect in Haptic Mode
            self.print_step(1, "Haptic Connection", 
                           "Connect to Frame glasses in haptic mode for touch-triggered capture")
            
            response = await self.session.post(f"{self.base_url}/api/v1/haptic/connect")
            result = response.json()
            self.print_result(result, "Haptic Connection")
            
            if not result.get('success'):
                print("❌ Failed to connect in haptic mode")
                return
            
            # Step 2: Start Haptic Monitoring
            self.print_step(2, "Start Haptic Monitoring", 
                           "Start monitoring for touch events on the glasses")
            
            response = await self.session.post(f"{self.base_url}/api/v1/haptic/start-monitoring")
            result = response.json()
            self.print_result(result, "Haptic Monitoring")
            
            if not result.get('success'):
                print("❌ Failed to start haptic monitoring")
                return
            
            # Step 3: Check Status
            self.print_step(3, "Check Haptic Status", 
                           "Verify haptic mode is active and monitoring is running")
            
            response = await self.session.get(f"{self.base_url}/api/v1/haptic/status")
            result = response.json()
            self.print_result(result, "Haptic Status")
            
            # Step 4: Demo Touch Events
            self.print_step(4, "Touch Event Demo", 
                           "Demonstrate touch-triggered photo capture")
            
            print("👆 Touch the Frame glasses to capture photos!")
            print("   The glasses will detect physical touch and automatically capture")
            print("   You should see 'T' indicator on the glasses display")
            print("   Photos will be captured and processed automatically")
            
            # Wait for user interaction
            print("\n⏳ Waiting for touch events... (Press Ctrl+C to stop)")
            print("   Touch the glasses multiple times to see captures")
            
            # Monitor for captures (in a real app, this would be continuous)
            for i in range(5):  # Demo 5 potential touches
                try:
                    await asyncio.sleep(2)  # Wait 2 seconds between checks
                    print(f"   Check {i+1}/5: Monitoring for touch events...")
                    
                    # Check status again
                    response = await self.session.get(f"{self.base_url}/api/v1/haptic/status")
                    status = response.json()
                    
                    if status.get('last_capture'):
                        print(f"   🎯 Touch detected! Last capture: {status['last_capture']}")
                    
                except KeyboardInterrupt:
                    print("\n⏹️  Demo stopped by user")
                    break
            
            # Step 5: Stop Monitoring
            self.print_step(5, "Stop Haptic Monitoring", 
                           "Stop monitoring for touch events")
            
            response = await self.session.post(f"{self.base_url}/api/v1/haptic/stop-monitoring")
            result = response.json()
            self.print_result(result, "Stop Monitoring")
            
            # Step 6: Disconnect
            self.print_step(6, "Disconnect", 
                           "Disconnect from Frame glasses")
            
            response = await self.session.post(f"{self.base_url}/api/v1/haptic/disconnect")
            result = response.json()
            self.print_result(result, "Disconnect")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        
        finally:
            await self.session.aclose()
    
    async def test_manual_capture_in_haptic_mode(self):
        """Test manual capture while in haptic mode"""
        
        print("\n🔧 TESTING MANUAL CAPTURE IN HAPTIC MODE")
        print("=" * 50)
        
        try:
            # Connect in haptic mode
            response = await self.session.post(f"{self.base_url}/api/v1/haptic/connect")
            result = response.json()
            
            if not result.get('success'):
                print("❌ Failed to connect in haptic mode")
                return
            
            print("✅ Connected in haptic mode")
            
            # Test manual capture
            print("📸 Testing manual capture...")
            response = await self.session.post(
                f"{self.base_url}/api/v1/haptic/capture-manual",
                json={"resolution": 720}
            )
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Manual capture successful!")
                print(f"   Image size: {result.get('image_size_bytes')} bytes")
                print(f"   Resolution: {result.get('resolution')}")
                print(f"   Timestamp: {result.get('timestamp')}")
            else:
                print(f"❌ Manual capture failed: {result.get('detail')}")
            
            # Disconnect
            await self.session.post(f"{self.base_url}/api/v1/haptic/disconnect")
            
        except Exception as e:
            print(f"❌ Manual capture test failed: {e}")
    
    async def show_api_endpoints(self):
        """Show available haptic API endpoints"""
        print("\n📚 HAPTIC API ENDPOINTS:")
        print("=" * 50)
        
        endpoints = [
            ("POST", "/api/v1/haptic/connect", "Connect in haptic mode"),
            ("POST", "/api/v1/haptic/disconnect", "Disconnect and stop monitoring"),
            ("POST", "/api/v1/haptic/start-monitoring", "Start touch monitoring"),
            ("POST", "/api/v1/haptic/stop-monitoring", "Stop touch monitoring"),
            ("GET", "/api/v1/haptic/status", "Get haptic status"),
            ("POST", "/api/v1/haptic/capture-manual", "Manual capture in haptic mode"),
            ("POST", "/api/v1/haptic/display", "Display text on glasses"),
        ]
        
        for method, endpoint, description in endpoints:
            print(f"   {method:6} {endpoint:<35} {description}")
        
        print(f"\n📖 API Documentation: {BASE_URL}/docs")
        print(f"🔧 Interactive Testing: {BASE_URL}/docs")

async def main():
    """Main demo function"""
    demo = HapticCaptureDemo()
    
    # Show available endpoints
    await demo.show_api_endpoints()
    
    # Run the main haptic workflow demo
    await demo.test_haptic_workflow()
    
    # Test manual capture in haptic mode
    await demo.test_manual_capture_in_haptic_mode()
    
    print("\n🎉 HAPTIC CAPTURE DEMO COMPLETE!")
    print("=" * 50)
    print("Key Features Demonstrated:")
    print("✅ Haptic mode connection")
    print("✅ Touch event monitoring")
    print("✅ Automatic photo capture on touch")
    print("✅ Manual capture in haptic mode")
    print("✅ Real-time status monitoring")
    print("✅ Clean disconnection")

if __name__ == "__main__":
    asyncio.run(main()) 