import subprocess
import requests
import time
import os

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

# 3. Upload the photo to the API
print("🔗 Uploading photo to API for analysis...")
url = "http://localhost:8000/api/v1/analysis/food-to-restaurant"
with open(filename, "rb") as img:
    files = {"image": img}
    response = requests.post(url, files=files)

# 4. Print the result
if response.ok:
    result = response.json()
    print("\n✅ Analysis Result:")
    print(result)
    if result.get("restaurant"):
        print(f"\n🍽️  Restaurant: {result['restaurant'].get('name')}")
        print(f"📍 Address: {result['restaurant'].get('address')}")
        print(f"🗺️  Maps Link: {result.get('maps_link')}")
else:
    print(f"❌ API Error: {response.status_code} - {response.text}") 