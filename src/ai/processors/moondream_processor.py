import httpx
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class MoondreamProcessor:
    """Processor for Moondream AI vision analysis"""
    
    def __init__(self):
        self.api_key = os.getenv("MOONDREAM_API_KEY")
        self.base_url = "https://api.moondream.ai"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_key:
            raise ValueError("MOONDREAM_API_KEY environment variable is required")
    
    async def analyze_food(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze food items in the image using Moondream AI
        
        Args:
            image_data: JPEG image bytes from the glasses
            
        Returns:
            Structured food analysis data
        """
        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Create food analysis prompt
        prompt = """
        Analyze this food image and provide detailed information about:
        1. All visible food items
        2. Estimated calories for each item
        3. Key nutrients (protein, carbs, fat, fiber)
        4. Any dietary restrictions (gluten, dairy, nuts, etc.)
        5. Portion size estimates
        
        Format the response as a structured analysis with clear food item identification.
        """
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "moondream2",
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
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.1
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse the AI response and structure it
            ai_response = result['choices'][0]['message']['content']
            structured_data = self._parse_food_analysis(ai_response)
            
            return {
                "success": True,
                "raw_response": ai_response,
                "structured_data": structured_data,
                "processing_time_ms": 0,  # TODO: Add timing
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def general_analysis(self, image_data: bytes, custom_prompt: str) -> Dict[str, Any]:
        """
        General image analysis with custom prompt
        
        Args:
            image_data: JPEG image bytes
            custom_prompt: Custom analysis prompt
            
        Returns:
            Analysis result
        """
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "moondream2",
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
                                    "text": custom_prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.1
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "response": result['choices'][0]['message']['content'],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_food_analysis(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse the AI response into structured food data
        
        Args:
            ai_response: Raw AI response text
            
        Returns:
            Structured food data
        """
        # This is a simplified parser - in production you'd want more robust parsing
        # or use the AI to return structured JSON directly
        
        food_items = []
        total_calories = 0
        dietary_restrictions = []
        
        # Basic parsing logic (enhance this based on actual AI responses)
        lines = ai_response.split('\n')
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for food items (this is a simplified approach)
            if any(keyword in line.lower() for keyword in ['calories', 'protein', 'carbs', 'fat']):
                if current_item:
                    food_items.append(current_item)
                current_item = {"name": line.split()[0], "details": line}
        
        if current_item:
            food_items.append(current_item)
        
        return {
            "food_items": food_items,
            "total_calories": total_calories,
            "dietary_restrictions": dietary_restrictions,
            "raw_analysis": ai_response
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose() 