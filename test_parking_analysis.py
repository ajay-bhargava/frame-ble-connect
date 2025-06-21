#!/usr/bin/env python3
"""
Test script for parking sign analysis feature
"""

import requests
import json
from pathlib import Path

def test_parking_sign_analysis():
    """Test the parking sign analysis endpoint"""
    
    print("🚗 Testing Parking Sign Analysis")
    print("=" * 50)
    
    # Use the existing captured image (assuming it's a parking sign)
    image_path = Path("captured_frame.jpg")
    if not image_path.exists():
        print("❌ No captured image found. Please capture a parking sign image first.")
        print("   Use: python src/connect/single_capture.py")
        return
    
    # Test the parking sign analysis endpoint
    url = "http://localhost:8000/api/v1/parking/analyze-sign"
    
    print(f"📸 Uploading image: {image_path}")
    print(f"🔗 Endpoint: {url}")
    
    with open(image_path, "rb") as f:
        files = {"image": ("parking_sign.jpg", f, "image/jpeg")}
        data = {"include_violations": "true"}
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Parking sign analysis successful!")
        print("\n📊 Analysis Results:")
        print("-" * 30)
        
        # Display OCR text
        ocr_text = result.get("ocr_text", "No text extracted")
        print(f"📝 OCR Text: {ocr_text}")
        
        # Display extracted data
        extracted_data = result.get("extracted_data", {})
        zone_number = extracted_data.get("zone_number")
        street_name = extracted_data.get("street_name")
        
        print(f"🔢 Zone Number: {zone_number or 'Not found'}")
        print(f"🏘️  Street Name: {street_name or 'Not found'}")
        
        # Display parking info
        parking_info = result.get("parking_info")
        if parking_info and parking_info.get("success"):
            meter_info = parking_info.get("meter_info", {})
            print(f"\n🅿️  Parking Information:")
            print(f"   Meter Number: {meter_info.get('meter_number', 'N/A')}")
            print(f"   Street: {meter_info.get('on_street', 'N/A')}")
            print(f"   Borough: {meter_info.get('borough', 'N/A')}")
            print(f"   Hours: {meter_info.get('meter_hours', 'N/A')}")
            print(f"   Status: {meter_info.get('status', 'N/A')}")
        else:
            print(f"\n❌ Parking Info: {parking_info.get('error', 'Failed to get parking info')}")
        
        # Display violation statistics
        violation_stats = result.get("violation_stats")
        if violation_stats and violation_stats.get("success"):
            stats = violation_stats.get("violation_statistics", {})
            print(f"\n🚨 Violation Statistics:")
            print(f"   Total Violations: {stats.get('total_violations', 'N/A')}")
            print(f"   Last 30 Days: {stats.get('violations_last_30_days', 'N/A')}")
            print(f"   Last 7 Days: {stats.get('violations_last_7_days', 'N/A')}")
            print(f"   Average Fine: ${stats.get('average_fine', 'N/A')}")
            print(f"   Risk Level: {stats.get('risk_level', 'N/A')}")
            
            # Display common violation types
            common_types = stats.get('common_violation_types', [])
            if common_types:
                print(f"   Common Violations:")
                for violation in common_types[:3]:  # Show top 3
                    print(f"     • {violation['type']}: {violation['count']} ({violation['percentage']}%)")
        else:
            print(f"\n❌ Violation Stats: {violation_stats.get('error', 'Failed to get violation stats')}")
        
        print(f"\n⏱️  Processing Time: {result.get('processing_time_ms', 0):.2f}ms")
        
    else:
        print(f"❌ Analysis failed with status code: {response.status_code}")
        print(f"Error: {response.text}")

def test_zone_lookup():
    """Test direct zone number lookup"""
    
    print("\n🔍 Testing Zone Number Lookup")
    print("=" * 30)
    
    # Test with the example zone number from the documentation
    zone_number = "106184"
    url = f"http://localhost:8000/api/v1/parking/zone/{zone_number}"
    
    print(f"🔢 Looking up zone: {zone_number}")
    print(f"🔗 Endpoint: {url}")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Zone lookup successful!")
        
        if result.get("success"):
            meter_info = result.get("meter_info", {})
            print(f"   Street: {meter_info.get('on_street', 'N/A')}")
            print(f"   Borough: {meter_info.get('borough', 'N/A')}")
            print(f"   Hours: {meter_info.get('meter_hours', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Zone lookup failed: {response.status_code}")
        print(f"Error: {response.text}")

def test_street_lookup():
    """Test direct street name lookup"""
    
    print("\n🏘️  Testing Street Name Lookup")
    print("=" * 30)
    
    # Test with a common NYC street
    street_name = "LITTLE WEST 12 STREET"
    url = f"http://localhost:8000/api/v1/parking/street/{street_name}"
    
    print(f"🏘️  Looking up street: {street_name}")
    print(f"🔗 Endpoint: {url}")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Street lookup successful!")
        
        if result.get("success"):
            meters = result.get("meters", [])
            print(f"   Found {len(meters)} parking meters")
            
            if meters:
                first_meter = meters[0]
                print(f"   First meter: {first_meter.get('meter_number', 'N/A')}")
                print(f"   Zone: {first_meter.get('pay_by_cell_number', 'N/A')}")
                print(f"   Hours: {first_meter.get('meter_hours', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Street lookup failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("🚗 NYC Parking Sign Analysis Test Suite")
    print("=" * 50)
    
    # Test parking sign analysis
    test_parking_sign_analysis()
    
    # Test direct API endpoints
    test_zone_lookup()
    test_street_lookup()
    
    print("\n✅ Test suite completed!")
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Parking Endpoints:")
    print("   • POST /api/v1/parking/analyze-sign - Analyze parking sign image")
    print("   • GET  /api/v1/parking/zone/{zone} - Lookup by zone number")
    print("   • GET  /api/v1/parking/street/{street} - Lookup by street name")
    print("   • POST /api/v1/parking/extract-text - Extract text only") 