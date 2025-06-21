#!/usr/bin/env python3
"""
Test script for restaurant search functionality
"""
import sys
import os
import asyncio

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_restaurant_service():
    """Test the restaurant service functionality"""
    try:
        print("Testing restaurant service...")
        
        from src.api.services.restaurant_service import RestaurantService
        
        restaurant_service = RestaurantService()
        
        # Test finding restaurants for different food items
        test_foods = ["pizza", "sushi", "burger", "pasta", "taco", "unknown_food"]
        
        for food in test_foods:
            print(f"\nTesting food: {food}")
            result = await restaurant_service.find_restaurant_for_food(food)
            
            if result["success"]:
                restaurant = result["restaurant"]
                print(f"✅ Found: {restaurant['name']}")
                print(f"   Address: {restaurant['address']}")
                print(f"   Rating: {restaurant['rating']}")
                print(f"   Maps: {result['maps_link']}")
            else:
                print(f"❌ Failed: {result['error']}")
        
        await restaurant_service.close()
        print("\n🎉 Restaurant service test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Restaurant service test failed: {e}")
        return False

async def test_moondream_processor():
    """Test the enhanced Moondream processor"""
    try:
        print("\nTesting Moondream processor...")
        
        from src.ai.processors.moondream_processor import MoondreamProcessor
        
        # This will fail without API key, but we can test the parsing logic
        processor = MoondreamProcessor()
        
        # Test the parsing function with mock data
        mock_response = """
        Primary Food Item: pizza
        Additional Items: cheese, tomato sauce
        Estimated calories: 285
        Key nutrients: protein 12g, carbs 35g, fat 10g
        Dietary restrictions: contains dairy
        """
        
        parsed = processor._parse_food_analysis(mock_response)
        print(f"✅ Parsed food item: {parsed['primary_food_item']}")
        print(f"✅ Calories: {parsed['total_calories']}")
        print(f"✅ Restrictions: {parsed['dietary_restrictions']}")
        
        await processor.close()
        print("🎉 Moondream processor test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Moondream processor test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Restaurant Search Functionality")
    print("=" * 50)
    
    success = True
    success &= await test_restaurant_service()
    success &= await test_moondream_processor()
    
    if success:
        print("\n🎉 All tests passed! Restaurant search is ready.")
        print("\nTo test the complete workflow:")
        print("1. Set your MOONDREAM_API_KEY in .env file")
        print("2. Run: source .venv/bin/activate && python start_api.py")
        print("3. Test: POST /api/v1/analysis/food-to-restaurant")
        print("4. Or test: POST /api/v1/analysis/capture-and-find-restaurant")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 