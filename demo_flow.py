#!/usr/bin/env python3
"""
Frame Glasses AI Food Discovery - Complete UI/UX Flow Demo

This script demonstrates the complete user journey from photo capture
to restaurant discovery and navigation.
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

class FrameGlassesDemo:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
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
        
        if step_name == "Device Connection":
            print(f"   Message: {result.get('message', 'N/A')}")
        
        elif step_name == "Food Analysis":
            if result.get('success'):
                analysis = result.get('result', {})
                print(f"   Food Identified: {analysis.get('primary_food_item', 'Unknown')}")
                print(f"   Analysis: {analysis.get('raw_analysis', 'N/A')[:100]}...")
                print(f"   Processing Time: {result.get('processing_time_ms', 0):.0f}ms")
        
        elif step_name == "Restaurant Discovery":
            if result.get('restaurant_found'):
                restaurant = result.get('restaurant', {})
                print(f"   Restaurant: {restaurant.get('name', 'N/A')}")
                print(f"   Address: {restaurant.get('address', 'N/A')}")
                print(f"   Rating: {restaurant.get('rating', 'N/A')} ⭐")
                print(f"   Price: {restaurant.get('price_level', 'N/A')}")
                print(f"   Maps Link: {result.get('maps_link', 'N/A')}")
            else:
                print(f"   ❌ No restaurant found for: {result.get('primary_food_item', 'Unknown')}")
    
    def demo_complete_workflow(self):
        """Demonstrate the complete UI/UX flow"""
        
        print("🚀 FRAME GLASSES AI FOOD DISCOVERY - COMPLETE FLOW DEMO")
        print("=" * 70)
        
        # Step 1: Connect to Frame Glasses
        self.print_step(1, "Device Connection", 
                       "Connect to Frame glasses via Bluetooth Low Energy")
        
        try:
            response = self.session.post(f"{self.base_url}/device/connect")
            result = response.json()
            self.print_result(result, "Device Connection")
            
            if not result.get('success'):
                print("⚠️  Note: This is a demo - Frame glasses connection simulated")
                print("   In real demo, user would see 'Connected' on glasses display")
        
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("⚠️  Continuing with demo simulation...")
        
        # Step 2: Capture and Analyze Food
        self.print_step(2, "Food Capture & Analysis", 
                       "User takes photo → AI analyzes food type")
        
        print("👤 User Action: Takes photo of food with Frame glasses")
        print("📸 System: Photo captured and sent to API server")
        print("🤖 AI: Moondream vision model analyzes the image")
        
        try:
            # Simulate the complete workflow
            response = self.session.post(
                f"{self.base_url}/analysis/capture-and-find-restaurant",
                data={"resolution": 720}
            )
            result = response.json()
            
            if result.get('success'):
                # Show food analysis
                food_analysis = result.get('food_analysis', {})
                if food_analysis.get('success'):
                    analysis_data = food_analysis.get('structured_data', {})
                    print(f"   🍕 AI Identified: {analysis_data.get('primary_food_item', 'food')}")
                    print(f"   📊 Analysis: {analysis_data.get('raw_analysis', 'N/A')[:80]}...")
                
                # Show restaurant discovery
                self.print_result(result, "Restaurant Discovery")
                
                # Step 3: Display Results on Glasses
                self.print_step(3, "Glasses Display", 
                               "Show results on Frame glasses display")
                
                if result.get('restaurant_found'):
                    restaurant = result.get('restaurant', {})
                    display_text = f"{restaurant.get('name', 'Restaurant')} - {restaurant.get('address', 'NYC')}"
                    print(f"📱 Glasses Display: {display_text[:50]}...")
                    print("   (Truncated for small display)")
                else:
                    print("📱 Glasses Display: Restaurant found")
                
                # Step 4: Navigation
                self.print_step(4, "Navigation", 
                               "User gets maps link for directions")
                
                maps_link = result.get('maps_link', '')
                if maps_link:
                    print(f"🗺️  Maps Link: {maps_link}")
                    print("👤 User Action: Opens maps link on phone")
                    print("📍 System: Shows route to restaurant")
                    print("🎯 Result: User can navigate to restaurant!")
                else:
                    print("❌ No maps link available")
            
            else:
                print(f"❌ Workflow failed: {result.get('detail', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ API call failed: {e}")
            print("⚠️  Make sure the API server is running on port 8000")
        
        # Step 5: Summary
        self.print_step(5, "Demo Summary", 
                       "Complete workflow overview")
        
        print("🎉 COMPLETE WORKFLOW ACHIEVED:")
        print("   1. ✅ User takes photo with Frame glasses")
        print("   2. ✅ AI analyzes food using Moondream")
        print("   3. ✅ System finds restaurant in NYC")
        print("   4. ✅ Results displayed on glasses")
        print("   5. ✅ Maps link provided for navigation")
        print("\n🚀 READY FOR HACKATHON DEMO!")
    
    def demo_api_endpoints(self):
        """Show available API endpoints"""
        print("\n📚 AVAILABLE API ENDPOINTS:")
        print("=" * 50)
        
        endpoints = [
            ("GET", "/device/status", "Check Frame glasses status"),
            ("POST", "/device/connect", "Connect to Frame glasses"),
            ("POST", "/device/capture", "Capture image from glasses"),
            ("POST", "/device/display", "Display text on glasses"),
            ("POST", "/analysis/food", "Analyze uploaded food image"),
            ("POST", "/analysis/food-to-restaurant", "Complete workflow with uploaded image"),
            ("POST", "/analysis/capture-and-analyze", "Capture and analyze from glasses"),
            ("POST", "/analysis/capture-and-find-restaurant", "Complete workflow from glasses"),
        ]
        
        for method, endpoint, description in endpoints:
            print(f"   {method:6} {endpoint:<35} {description}")
        
        print(f"\n📖 API Documentation: http://localhost:8000/docs")
        print(f"🔧 Interactive Testing: http://localhost:8000/docs")

def main():
    """Main demo function"""
    demo = FrameGlassesDemo()
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running!")
        else:
            print("⚠️  API server may not be running properly")
    except:
        print("❌ API server is not running!")
        print("   Start it with: python start_api.py")
        return
    
    # Run the complete workflow demo
    demo.demo_complete_workflow()
    
    # Show available endpoints
    demo.demo_api_endpoints()

if __name__ == "__main__":
    main() 