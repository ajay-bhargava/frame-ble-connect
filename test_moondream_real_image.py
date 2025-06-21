#!/usr/bin/env python3
"""
Test Moondream API with a real image file
"""
import asyncio
import httpx
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_with_real_image():
    """Test Moondream API with a real image"""
    
    api_key = os.getenv("MOONDREAM_API_KEY")
    if not api_key:
        print("❌ MOONDREAM_API_KEY not found in environment")
        return
    
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-20:]}")
    
    # Try to use the image.b64 file if it exists
    image_path = "image.b64"
    if not os.path.exists(image_path):
        print(f"❌ {image_path} not found")
        return
    
    try:
        with open(image_path, 'r') as f:
            image_b64 = f.read().strip()
        
        print(f"📸 Loaded image from {image_path}")
        print(f"📏 Image base64 length: {len(image_b64)} characters")
        
        question = "What food is shown in this image? Please identify the main food item."
        
        client = httpx.AsyncClient(timeout=30.0)
        
        # Try the OpenAI-compatible format
        payload = {
            "model": "moondream-2B",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.1
        }
        
        print(f"🧪 Testing with real image...")
        print(f"📦 Payload size: {len(json.dumps(payload))} characters")
        
        response = await client.post(
            "https://api.moondream.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🤖 AI Response: {result['choices'][0]['message']['content']}")
        else:
            print("❌ API call failed")
            
        await client.aclose()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_with_real_image()) 