#!/usr/bin/env python3
"""
Debug script to test Moondream API directly
"""
import asyncio
import httpx
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_moondream_api():
    """Test different Moondream API formats"""
    
    api_key = os.getenv("MOONDREAM_API_KEY")
    if not api_key:
        print("❌ MOONDREAM_API_KEY not found in environment")
        return
    
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-20:]}")
    print(f"📏 Key length: {len(api_key)} characters")
    
    # Create a simple test image (1x1 pixel JPEG)
    test_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    image_b64 = base64.b64encode(test_image).decode('utf-8')
    question = "What do you see in this image?"
    
    client = httpx.AsyncClient(timeout=30.0)
    
    # Test different payload formats
    formats = [
        {
            "name": "OpenAI-compatible format",
            "payload": {
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
                "max_tokens": 100,
                "temperature": 0.1
            }
        },
        {
            "name": "Direct image format",
            "payload": {
                "model": "moondream-2B",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": f"data:image/jpeg;base64,{image_b64}"
                            },
                            {
                                "type": "text",
                                "text": question
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
        },
        {
            "name": "Simple text-only test",
            "payload": {
                "model": "moondream-2B",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, can you respond to this text message?"
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
        }
    ]
    
    for i, format_test in enumerate(formats, 1):
        print(f"\n🧪 Test {i}: {format_test['name']}")
        print(f"📦 Payload structure: {json.dumps(format_test['payload'], indent=2)}")
        
        try:
            response = await client.post(
                "https://api.moondream.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=format_test['payload']
            )
            
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 AI Response: {result['choices'][0]['message']['content']}")
                break
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_moondream_api()) 