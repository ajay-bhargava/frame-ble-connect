#!/usr/bin/env python3
"""
Test script for enhanced food analysis with structured nutritional and dietary information
"""

import requests
import json
from pathlib import Path

def test_enhanced_food_analysis():
    """Test the enhanced food analysis endpoint"""
    
    # Test with a food image
    print("🍕 Testing Enhanced Food Analysis")
    print("=" * 50)
    
    # Use the existing captured image
    image_path = Path("captured_frame.jpg")
    if not image_path.exists():
        print("❌ No captured image found. Please capture an image first.")
        return
    
    # Upload and analyze
    url = "http://localhost:8000/api/v1/analysis/upload-and-analyze"
    
    with open(image_path, "rb") as f:
        files = {"image": ("food.jpg", f, "image/jpeg")}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Analysis successful!")
        print(f"📊 Image Type: {result.get('image_type', 'unknown')}")
        print(f"🔍 Analysis Type: {result.get('analysis_type', 'unknown')}")
        print()
        
        if result.get('image_type') == 'food':
            print("🍽️ FOOD ANALYSIS RESULTS:")
            print(f"   Primary Food Item: {result.get('primary_food_item', 'unknown')}")
            print(f"   Health Assessment: {result.get('health_assessment', 'unknown')}")
            
            # Ingredients
            ingredients = result.get('ingredients', [])
            if ingredients:
                print(f"   Ingredients: {', '.join(ingredients)}")
            
            # Nutritional info
            nutrition = result.get('nutritional_info', {})
            if nutrition:
                print("   Nutritional Information:")
                for nutrient, value in nutrition.items():
                    print(f"     {nutrient.capitalize()}: {value}")
            
            # Dietary risks
            risks = result.get('dietary_risks', [])
            if risks:
                print(f"   ⚠️  Dietary Risks: {', '.join(risks)}")
            else:
                print("   ✅ No dietary risks detected")
            
            # Raw analysis
            print(f"\n📝 Raw Analysis:")
            print(f"   {result.get('result', {}).get('raw_analysis', 'No analysis available')}")
            
        elif result.get('image_type') == 'street sign':
            print("🚦 STREET SIGN ANALYSIS:")
            extracted_text = result.get('extracted_text', '')
            if extracted_text:
                print(f"   Extracted Text: {extracted_text}")
            else:
                print("   No text extracted")
                
            # Raw analysis
            print(f"\n📝 Raw Analysis:")
            print(f"   {result.get('result', {}).get('raw_analysis', 'No analysis available')}")
        
        else:
            print("❓ Unknown image type")
            print(f"   Raw Response: {result.get('result', {}).get('raw_analysis', 'No analysis available')}")
        
        print(f"\n⏱️  Processing Time: {result.get('processing_time_ms', 0):.2f}ms")
        
    else:
        print(f"❌ Analysis failed: {response.status_code}")
        print(f"   Error: {response.text}")

def test_text_extraction():
    """Test text extraction with a sign image"""
    print("\n🚦 Testing Text Extraction")
    print("=" * 50)
    
    # This would test with a sign image
    # For now, we'll use the same image to see how it handles text detection
    image_path = Path("captured_frame.jpg")
    if not image_path.exists():
        print("❌ No captured image found.")
        return
    
    url = "http://localhost:8000/api/v1/analysis/query"
    
    with open(image_path, "rb") as f:
        files = {"image": ("sign.jpg", f, "image/jpeg")}
        data = {"question": "Extract all text you can see in this image. Format as: Text found: [list all text content]"}
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Text extraction successful!")
        print(f"📝 Answer: {result.get('answer', 'No answer')}")
    else:
        print(f"❌ Text extraction failed: {response.status_code}")

if __name__ == "__main__":
    test_enhanced_food_analysis()
    test_text_extraction() 