#!/usr/bin/env python3
"""
Test static file serving
"""
import asyncio
import httpx
import base64
import os
from pathlib import Path

async def test_static_serving():
    """Test if static files are being served correctly"""
    
    # Create a test image in the static directory
    static_dir = Path("static/images")
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple test image (1x1 pixel JPEG)
    test_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    test_filename = "test_image.jpg"
    test_filepath = static_dir / test_filename
    
    with open(test_filepath, 'wb') as f:
        f.write(test_image)
    
    print(f"💾 Created test image: {test_filepath}")
    
    # Test if the server is running and serving static files
    client = httpx.AsyncClient(timeout=10.0)
    
    try:
        # Test the static file URL
        static_url = f"http://localhost:8000/static/images/{test_filename}"
        print(f"🔗 Testing URL: {static_url}")
        
        response = await client.get(static_url)
        
        if response.status_code == 200:
            print(f"✅ Static file serving works! Status: {response.status_code}")
            print(f"📏 Response size: {len(response.content)} bytes")
        else:
            print(f"❌ Static file serving failed. Status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except httpx.ConnectError:
        print("❌ Could not connect to server. Make sure the API server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    await client.aclose()
    
    # Clean up test file
    if test_filepath.exists():
        test_filepath.unlink()
        print(f"🧹 Cleaned up test file")

if __name__ == "__main__":
    asyncio.run(test_static_serving()) 