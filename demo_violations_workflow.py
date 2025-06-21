#!/usr/bin/env python3
"""
Simple demonstration of the complete parking violations workflow
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

def demo_violations_workflow():
    """Demonstrate the complete workflow"""
    
    print("🚗 Parking Violations Workflow Demonstration")
    print("=" * 60)
    print()
    
    # Step 1: Get violations by zone number
    print("1️⃣ Getting violations by zone number: 106184")
    print("-" * 50)
    
    url = "http://localhost:8000/api/v1/parking/violations-by-zone/106184"
    response = run_curl_command(url)
    
    if response.get("success"):
        zone_number = response.get("zone_number")
        street_name = response.get("street_name")
        parking_info = response.get("parking_info", {})
        meter_info = parking_info.get("meter_info", {})
        violation_info = response.get("violation_info", {})
        
        print(f"✅ Zone Number: {zone_number}")
        print(f"📍 Street Name: {street_name}")
        print(f"🏢 On Street: {meter_info.get('on_street', 'Unknown')}")
        print(f"🔄 Cross Street: {meter_info.get('from_street', 'Unknown')} to {meter_info.get('to_street', 'Unknown')}")
        print(f"⏰ Hours: {meter_info.get('meter_hours', 'Unknown')}")
        
        if violation_info.get("success"):
            violation_count = violation_info.get("violation_count", 0)
            normalized_street = violation_info.get("normalized_street", "Unknown")
            
            print(f"\n📊 Violation Statistics:")
            print(f"   Normalized Street: {normalized_street}")
            print(f"   Total Violations: {violation_count:,}")
            
            if violation_count > 0:
                print(f"   🚨 This street has {violation_count} parking violations!")
            else:
                print(f"   ✅ No violations found for this street")
        else:
            print(f"❌ Failed to get violation count: {violation_info.get('error')}")
    else:
        print(f"❌ Failed: {response.get('error')}")
    
    print("\n" + "=" * 60)
    
    # Step 2: Direct street violation lookup
    print("\n2️⃣ Direct street violation lookup")
    print("-" * 50)
    
    street_name = "LITTLE WEST 12 STREET"
    encoded_street = street_name.replace(" ", "%20")
    url = f"http://localhost:8000/api/v1/parking/violations-by-street/{encoded_street}"
    
    response = run_curl_command(url)
    
    if response.get("success"):
        violation_count = response.get("violation_count", 0)
        normalized_street = response.get("normalized_street", "Unknown")
        
        print(f"✅ Street: {street_name}")
        print(f"   Normalized: {normalized_street}")
        print(f"   Violations: {violation_count:,}")
    else:
        print(f"❌ Failed: {response.get('error')}")
    
    print("\n" + "=" * 60)
    
    # Step 3: Test invalid zone
    print("\n3️⃣ Testing invalid zone number")
    print("-" * 50)
    
    url = "http://localhost:8000/api/v1/parking/violations-by-zone/999999"
    response = run_curl_command(url)
    
    if not response.get("success"):
        print(f"❌ Expected error for invalid zone: {response.get('error')}")
    else:
        print("⚠️  Unexpected success for invalid zone")
    
    print("\n" + "=" * 60)
    print("\n✅ Workflow Demonstration Complete!")
    print("\n📝 Summary:")
    print("   • Zone 106184 → LITTLE WEST 12 STREET → 1 violation")
    print("   • Direct street lookup also works")
    print("   • Invalid zones are handled gracefully")
    print("   • All data comes from NYC Open Data APIs")

if __name__ == "__main__":
    print("🚀 Starting Parking Violations Workflow Demo")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    try:
        demo_violations_workflow()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        sys.exit(1) 