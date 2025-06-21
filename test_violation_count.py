#!/usr/bin/env python3
"""
Simple test for the new violation count endpoint
"""

import subprocess
import json
import sys

def run_curl_command(url):
    """Run a curl command and return the JSON response"""
    try:
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": f"curl failed: {result.stderr}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def test_violation_count():
    """Test the new violation count endpoint"""
    
    print("🚗 Testing Violation Count Endpoint")
    print("=" * 50)
    print()
    
    # Test valid zone
    print("1️⃣ Testing zone 106184")
    print("-" * 30)
    
    url = "http://localhost:8000/api/v1/parking/violation-count/106184"
    response = run_curl_command(url)
    
    if response.get("success"):
        zone_number = response.get("zone_number")
        street_name = response.get("street_name")
        violation_count = response.get("violation_count")
        data_freshness = response.get("data_freshness")
        
        print(f"✅ Zone: {zone_number}")
        print(f"📍 Street: {street_name}")
        print(f"🚨 Violations: {violation_count}")
        print(f"📅 Data: {data_freshness}")
    else:
        print(f"❌ Failed: {response.get('error')}")
    
    print("\n" + "=" * 50)
    
    # Test invalid zone
    print("\n2️⃣ Testing invalid zone 999999")
    print("-" * 30)
    
    url = "http://localhost:8000/api/v1/parking/violation-count/999999"
    response = run_curl_command(url)
    
    if not response.get("success"):
        print(f"❌ Expected error: {response.get('error')}")
    else:
        print("⚠️  Unexpected success for invalid zone")
    
    print("\n" + "=" * 50)
    print("\n✅ Test completed!")
    print("\n📝 Summary:")
    print("   • Simple endpoint: /api/v1/parking/violation-count/{zone_number}")
    print("   • Returns: zone, street, violation count, data freshness")
    print("   • Much cleaner than the full violations-by-zone endpoint")

if __name__ == "__main__":
    print("🚀 Starting Violation Count Test")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    try:
        test_violation_count()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1) 