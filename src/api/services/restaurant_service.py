import httpx
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RestaurantService:
    """Service for finding restaurants based on food items"""
    
    def __init__(self):
        # You can use Google Places API, Yelp API, or other services
        # For MVP, we'll use a simple approach with Google Places API
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.base_location = "New York, NY"  # Static starting location
        self.client = httpx.AsyncClient(timeout=10.0)
        
    async def find_restaurant_for_food(self, food_item: str) -> Dict[str, Any]:
        """
        Find a restaurant in NYC that serves the given food item
        
        Args:
            food_item: Name of the food item (e.g., "pizza", "sushi")
            
        Returns:
            Restaurant information with maps link
        """
        try:
            # For MVP, we'll use a simplified approach
            # In production, you'd use Google Places API or Yelp API
            
            # Create a search query
            search_query = f"{food_item} restaurant {self.base_location}"
            
            # For now, return a mock response with a maps link
            # In production, you'd make an API call to Google Places
            restaurant_data = await self._get_restaurant_data(food_item, search_query)
            
            return {
                "success": True,
                "food_item": food_item,
                "restaurant": restaurant_data,
                "maps_link": restaurant_data["maps_link"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "food_item": food_item,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_restaurant_data(self, food_item: str, search_query: str) -> Dict[str, Any]:
        """
        Get restaurant data - for MVP, returns mock data
        In production, this would call Google Places API
        """
        
        # Mock restaurant data for common food items
        restaurant_mock_data = {
            "pizza": {
                "name": "Joe's Pizza",
                "address": "123 Bleecker St, New York, NY 10012",
                "rating": 4.5,
                "price_level": "$$",
                "maps_link": "https://maps.google.com/?q=Joe's+Pizza+123+Bleecker+St+New+York+NY"
            },
            "sushi": {
                "name": "Sushi Nakazawa",
                "address": "23 Commerce St, New York, NY 10014",
                "rating": 4.8,
                "price_level": "$$$",
                "maps_link": "https://maps.google.com/?q=Sushi+Nakazawa+23+Commerce+St+New+York+NY"
            },
            "burger": {
                "name": "Shake Shack",
                "address": "Madison Square Park, New York, NY 10010",
                "rating": 4.3,
                "price_level": "$$",
                "maps_link": "https://maps.google.com/?q=Shake+Shack+Madison+Square+Park+New+York+NY"
            },
            "pasta": {
                "name": "Carbone",
                "address": "181 Thompson St, New York, NY 10012",
                "rating": 4.7,
                "price_level": "$$$",
                "maps_link": "https://maps.google.com/?q=Carbone+181+Thompson+St+New+York+NY"
            },
            "taco": {
                "name": "Los Tacos No. 1",
                "address": "229 E 43rd St, New York, NY 10017",
                "rating": 4.4,
                "price_level": "$",
                "maps_link": "https://maps.google.com/?q=Los+Tacos+No+1+229+E+43rd+St+New+York+NY"
            }
        }
        
        # Try to find exact match first
        if food_item.lower() in restaurant_mock_data:
            return restaurant_mock_data[food_item.lower()]
        
        # If no exact match, find the best partial match
        for key, value in restaurant_mock_data.items():
            if key in food_item.lower() or food_item.lower() in key:
                return value
        
        # Default fallback
        return {
            "name": "Local Restaurant",
            "address": "New York, NY",
            "rating": 4.0,
            "price_level": "$$",
            "maps_link": f"https://maps.google.com/?q={food_item}+restaurant+New+York+NY"
        }
    
    async def get_maps_directions(self, destination: str) -> Dict[str, Any]:
        """
        Get directions to the restaurant
        
        Args:
            destination: Restaurant address or name
            
        Returns:
            Directions information
        """
        try:
            # Create a Google Maps directions link
            directions_link = f"https://maps.google.com/directions?daddr={destination}&saddr={self.base_location}"
            
            return {
                "success": True,
                "directions_link": directions_link,
                "from": self.base_location,
                "to": destination,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose() 