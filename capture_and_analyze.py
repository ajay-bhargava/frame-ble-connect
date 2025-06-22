import subprocess
import requests
import time
import os
import asyncio
from frame_ble import FrameBle
import re

async def send_to_glasses(text):
    """Send text to Frame glasses display"""
    frame = FrameBle()
    try:
        await frame.connect()
        # Send text to glasses display
        lua_command = f"frame.display.text('{text}', 1, 1);frame.display.show();print(0)"
        await frame.send_lua(lua_command, await_print=True)
        print(f"📱 Sent to glasses: {text}")
        await frame.disconnect()
    except Exception as e:
        print(f"❌ Could not connect to Frame glasses: {e}")

def extract_zone_number(extracted_text):
    """Extract zone number (5-6 digits) from the sign text"""
    # Look for 5-6 digit numbers (typical for pay-by-cell zone numbers)
    numbers = re.findall(r'\b\d{5,6}\b', extracted_text)
    if numbers:
        # Return the first 5-6 digit number found (likely the zone number)
        return numbers[0]
    
    # Fallback: look for any number sequence
    all_numbers = re.findall(r'\d+', extracted_text)
    if all_numbers:
        return all_numbers[0]
    
    return None

def get_violation_count_by_zone(zone_number):
    """Get violation count from parking API by zone number"""
    try:
        url = f"http://localhost:8000/api/v1/parking/violation-count/{zone_number}"
        response = requests.get(url)
        
        if response.ok:
            result = response.json()
            if result.get("success"):
                return result.get("violation_count", 0), result.get("street_name", "Unknown Street")
            else:
                print(f"❌ API Error: {result.get('error', 'Unknown error')}")
                return None, None
        else:
            print(f"❌ HTTP Error: {response.status_code} - {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None, None

def main():
    # 1. Capture the photo
    print("📸 Capturing photo with Frame glasses...")
    subprocess.run(["python", "src/connect/single_capture.py"], check=True)

    # 2. Wait for the file to be saved
    filename = "captured_frame.jpg"
    for _ in range(10):
        if os.path.exists(filename):
            break
        time.sleep(0.5)
    else:
        print("❌ Photo was not saved.")
        exit(1)

    # 3. Upload the photo to the API for sign analysis
    print("🔗 Uploading photo to API for sign analysis...")
    url = "http://localhost:8000/api/v1/analysis/sign"
    with open(filename, "rb") as img:
        files = {"image": (filename, img, "image/jpeg")}
        response = requests.post(url, files=files)

    # 4. Process the result
    if response.ok:
        result = response.json()
        extracted_text = result.get('extracted_text', 'No text found')
        
        print("\n✅ Sign Analysis Result:")
        print(f"🏷️  Extracted Text: {extracted_text}")
        print(f"⏱️  Processing Time: {result.get('processing_time_ms', 0):.0f}ms")
        
        # Extract zone number from sign text
        zone_number = extract_zone_number(extracted_text)
        
        if zone_number:
            print(f"🅿️  Zone Number: {zone_number}")
            
            # Get violation count from parking API
            print("🔍 Getting violation count from parking API...")
            violation_count, street_name = get_violation_count_by_zone(zone_number)
            
            if violation_count is not None:
                print(f"⚠️  Violations Count: {violation_count}")
                print(f"🛣️  Street: {street_name}")
                
                # Send violations count to glasses
                print("📱 Sending violations count to Frame glasses...")
                asyncio.run(send_to_glasses(f"Zone {zone_number}: {violation_count} violations"))
            else:
                print("❌ Could not get violation count")
                asyncio.run(send_to_glasses(f"Zone {zone_number}: No data"))
        else:
            print("❌ No zone number found in sign text")
            asyncio.run(send_to_glasses("No zone number found"))
        
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        # Send error to glasses
        asyncio.run(send_to_glasses("Analysis Failed"))

if __name__ == "__main__":
    main() 