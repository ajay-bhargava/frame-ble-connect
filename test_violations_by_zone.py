#!/usr/bin/env python3
"""
Test script for the complete parking violations workflow:
1. Get address from pay-by-cell number (106184)
2. Use that address to get parking violation count
"""

import asyncio
import httpx
import json
from urllib.parse import quote

BASE_URL = "http://localhost:8000"

async def test_violations_by_zone():
    """Test the complete workflow from zone number to violation count"""
    
    async with httpx.AsyncClient() as client:
        print("🚗 Testing Complete Parking Violations Workflow")
        print("=" * 60)
        
        # Test zone number 106184 (which we know maps to LITTLE WEST 12 STREET)
        zone_number = "106184"
        
        print(f"\n1️⃣ Getting violations by zone number: {zone_number}")
        print("-" * 50)
        
        url = f"{BASE_URL}/api/v1/parking/violations-by-zone/{zone_number}"
        response = await client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Zone Number: {data.get('zone_number')}")
            
            # Extract parking info
            parking_info = data.get('parking_info', {})
            meter_info = parking_info.get('meter_info', {})
            street_name = data.get('street_name', 'Unknown')
            
            print(f"Street Name: {street_name}")
            print(f"On Street: {meter_info.get('on_street', 'Unknown')}")
            print(f"Cross Street: {meter_info.get('cross_street', 'Unknown')}")
            
            # Extract violation info
            violation_info = data.get('violation_info', {})
            if violation_info.get('success'):
                violation_count = violation_info.get('violation_count', 0)
                normalized_street = violation_info.get('normalized_street', 'Unknown')
                
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
            print(f"❌ Failed to get violations by zone: {response.status_code}")
            print(response.text)
        
        print("\n" + "=" * 60)
        
        # Test direct street violation lookup
        print(f"\n2️⃣ Testing direct street violation lookup")
        print("-" * 50)
        
        street_name = "LITTLE WEST 12 STREET"
        encoded_street = quote(street_name)
        url = f"{BASE_URL}/api/v1/parking/violations-by-street/{encoded_street}"
        
        response = await client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                violation_count = data.get('violation_count', 0)
                normalized_street = data.get('normalized_street', 'Unknown')
                
                print(f"✅ Street: {street_name}")
                print(f"   Normalized: {normalized_street}")
                print(f"   Violations: {violation_count:,}")
            else:
                print(f"❌ Failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)

async def test_multiple_zones():
    """Test multiple zone numbers to see different results"""
    
    async with httpx.AsyncClient() as client:
        print("\n\n🔍 Testing Multiple Zone Numbers")
        print("=" * 60)
        
        # Test a few different zone numbers
        test_zones = ["106184", "999999", "123456"]
        
        for zone_number in test_zones:
            print(f"\n📍 Testing Zone: {zone_number}")
            print("-" * 30)
            
            url = f"{BASE_URL}/api/v1/parking/violations-by-zone/{zone_number}"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    street_name = data.get('street_name', 'Unknown')
                    violation_count = data.get('violation_info', {}).get('violation_count', 0)
                    
                    print(f"   Street: {street_name}")
                    print(f"   Violations: {violation_count:,}")
                else:
                    print(f"   ❌ Error: {data.get('error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Starting Parking Violations Workflow Test")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    asyncio.run(test_violations_by_zone())
    asyncio.run(test_multiple_zones())
    
    print("\n✅ Test completed!")
    print("\n📝 Summary:")
    print("   - Zone 106184 → LITTLE WEST 12 STREET → Violation count")
    print("   - Direct street violation lookup also available")
    print("   - All data comes from NYC Open Data APIs") 