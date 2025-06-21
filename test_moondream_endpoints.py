#!/usr/bin/env python3
"""
Test script for the new Moondream API endpoints

This script demonstrates all four new Moondream endpoints:
1. /analysis/caption - Generate image captions
2. /analysis/query - Visual question answering
3. /analysis/detect - Object detection with bounding boxes
4. /analysis/point - Object localization with center points

Requirements:
- API server running on localhost:8000
- Test image file (JPEG, PNG, or GIF)
- httpx for async HTTP requests

Usage:
    python test_moondream_endpoints.py [image_path]

If no image path is provided, the script will try to use a default test image.
"""

import asyncio
import httpx
import sys
from pathlib import Path
import json
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
ANALYSIS_ENDPOINT = f"{BASE_URL}/analysis"

# Test cases for different endpoints
TEST_CASES = {
    "caption": [
        {"length": "short", "description": "Brief caption"},
        {"length": "normal", "description": "Detailed caption"}
    ],
    "query": [
        {"question": "What is the main subject of this image?", "description": "General question"},
        {"question": "What colors are prominent in this image?", "description": "Color analysis"},
        {"question": "Is this image taken indoors or outdoors?", "description": "Location inference"},
        {"question": "What time of day was this photo taken?", "description": "Time analysis"}
    ],
    "detect": [
        {"object_type": "person", "description": "Detect people"},
        {"object_type": "face", "description": "Detect faces"},
        {"object_type": "car", "description": "Detect vehicles"},
        {"object_type": "food", "description": "Detect food items"},
        {"object_type": "text", "description": "Detect text regions"}
    ],
    "point": [
        {"object_type": "person", "description": "Locate people center points"},
        {"object_type": "face", "description": "Locate face center points"},
        {"object_type": "car", "description": "Locate vehicle center points"},
        {"object_type": "food", "description": "Locate food center points"}
    ]
}

class MoondreamTester:
    """
    Comprehensive tester for Moondream API endpoints
    
    This class provides methods to test all four Moondream endpoints with various
    parameters and scenarios. It includes error handling, performance timing,
    and result visualization.
    """
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.results = {}
    
    async def test_caption_endpoint(self, image_path: Path) -> Dict[str, Any]:
        """
        Test the /analysis/caption endpoint with different length parameters
        
        Args:
            image_path: Path to test image file
            
        Returns:
            Dictionary containing test results for both short and normal captions
        """
        print("🖼️  Testing Caption Endpoint")
        print("=" * 50)
        
        results = {}
        
        for test_case in TEST_CASES["caption"]:
            length = test_case["length"]
            description = test_case["description"]
            
            print(f"\n📝 Testing {description} (length={length})")
            
            try:
                with open(image_path, 'rb') as image_file:
                    files = {"image": image_file}
                    data = {"length": length, "stream": False}
                    
                    response = await self.client.post(
                        f"{self.base_url}/analysis/caption",
                        files=files,
                        data=data
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                results[length] = result
                
                # Display results
                if result["success"]:
                    print(f"✅ Success!")
                    print(f"   Caption: {result['caption']}")
                    print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
                    print(f"   Request ID: {result.get('request_id', 'N/A')}")
                else:
                    print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                results[length] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_query_endpoint(self, image_path: Path) -> Dict[str, Any]:
        """
        Test the /analysis/query endpoint with various questions
        
        Args:
            image_path: Path to test image file
            
        Returns:
            Dictionary containing test results for different questions
        """
        print("\n❓ Testing Query Endpoint (Visual Question Answering)")
        print("=" * 50)
        
        results = {}
        
        for i, test_case in enumerate(TEST_CASES["query"]):
            question = test_case["question"]
            description = test_case["description"]
            
            print(f"\n🤔 Testing {description}")
            print(f"   Question: '{question}'")
            
            try:
                with open(image_path, 'rb') as image_file:
                    files = {"image": image_file}
                    data = {"question": question, "stream": False}
                    
                    response = await self.client.post(
                        f"{self.base_url}/analysis/query",
                        files=files,
                        data=data
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                results[f"question_{i+1}"] = result
                
                # Display results
                if result["success"]:
                    print(f"✅ Success!")
                    print(f"   Answer: {result['answer']}")
                    print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
                    print(f"   Request ID: {result.get('request_id', 'N/A')}")
                else:
                    print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                results[f"question_{i+1}"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_detect_endpoint(self, image_path: Path) -> Dict[str, Any]:
        """
        Test the /analysis/detect endpoint with different object types
        
        Args:
            image_path: Path to test image file
            
        Returns:
            Dictionary containing detection results for different object types
        """
        print("\n🔍 Testing Detect Endpoint (Object Detection)")
        print("=" * 50)
        
        results = {}
        
        for test_case in TEST_CASES["detect"]:
            object_type = test_case["object_type"]
            description = test_case["description"]
            
            print(f"\n🎯 Testing {description}")
            print(f"   Object type: '{object_type}'")
            
            try:
                with open(image_path, 'rb') as image_file:
                    files = {"image": image_file}
                    data = {"object_type": object_type}
                    
                    response = await self.client.post(
                        f"{self.base_url}/analysis/detect",
                        files=files,
                        data=data
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                results[object_type] = result
                
                # Display results
                if result["success"]:
                    count = result["count"]
                    print(f"✅ Success! Found {count} {object_type}(s)")
                    
                    for i, obj in enumerate(result["objects"]):
                        print(f"   Object {i+1}: bbox({obj['x_min']:.3f}, {obj['y_min']:.3f}, {obj['x_max']:.3f}, {obj['y_max']:.3f})")
                    
                    print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
                    print(f"   Request ID: {result.get('request_id', 'N/A')}")
                else:
                    print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                results[object_type] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_point_endpoint(self, image_path: Path) -> Dict[str, Any]:
        """
        Test the /analysis/point endpoint with different object types
        
        Args:
            image_path: Path to test image file
            
        Returns:
            Dictionary containing pointing results for different object types
        """
        print("\n📍 Testing Point Endpoint (Object Localization)")
        print("=" * 50)
        
        results = {}
        
        for test_case in TEST_CASES["point"]:
            object_type = test_case["object_type"]
            description = test_case["description"]
            
            print(f"\n🎯 Testing {description}")
            print(f"   Object type: '{object_type}'")
            
            try:
                with open(image_path, 'rb') as image_file:
                    files = {"image": image_file}
                    data = {"object_type": object_type}
                    
                    response = await self.client.post(
                        f"{self.base_url}/analysis/point",
                        files=files,
                        data=data
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                results[object_type] = result
                
                # Display results
                if result["success"]:
                    count = result["count"]
                    print(f"✅ Success! Found {count} {object_type}(s)")
                    
                    for i, point in enumerate(result["points"]):
                        print(f"   Point {i+1}: center({point['x']:.3f}, {point['y']:.3f})")
                    
                    print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
                    print(f"   Request ID: {result.get('request_id', 'N/A')}")
                else:
                    print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                results[object_type] = {"success": False, "error": str(e)}
        
        return results
    
    async def run_full_test_suite(self, image_path: Path) -> Dict[str, Any]:
        """
        Run comprehensive tests on all four Moondream endpoints
        
        Args:
            image_path: Path to test image file
            
        Returns:
            Complete test results for all endpoints
        """
        print("🚀 Starting Comprehensive Moondream API Test Suite")
        print("=" * 60)
        print(f"Test image: {image_path}")
        print(f"API base URL: {self.base_url}")
        print()
        
        # Check if image exists
        if not image_path.exists():
            raise FileNotFoundError(f"Test image not found: {image_path}")
        
        # Check if API server is running
        try:
            health_response = await self.client.get(f"{self.base_url}/")
            print(f"✅ API server is running (status: {health_response.status_code})")
        except Exception as e:
            print(f"❌ Cannot connect to API server: {str(e)}")
            return {"error": "API server not accessible"}
        
        # Run all tests
        all_results = {}
        
        try:
            # Test 1: Caption endpoint
            all_results["caption"] = await self.test_caption_endpoint(image_path)
            
            # Test 2: Query endpoint  
            all_results["query"] = await self.test_query_endpoint(image_path)
            
            # Test 3: Detect endpoint
            all_results["detect"] = await self.test_detect_endpoint(image_path)
            
            # Test 4: Point endpoint
            all_results["point"] = await self.test_point_endpoint(image_path)
            
            # Summary
            self._print_test_summary(all_results)
            
            return all_results
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            return {"error": str(e)}
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of all test results"""
        print("\n📊 Test Summary")
        print("=" * 60)
        
        total_tests = 0
        successful_tests = 0
        
        for endpoint, endpoint_results in results.items():
            if isinstance(endpoint_results, dict):
                endpoint_total = 0
                endpoint_success = 0
                
                for test_name, test_result in endpoint_results.items():
                    if isinstance(test_result, dict) and "success" in test_result:
                        endpoint_total += 1
                        total_tests += 1
                        if test_result["success"]:
                            endpoint_success += 1
                            successful_tests += 1
                
                success_rate = (endpoint_success / endpoint_total * 100) if endpoint_total > 0 else 0
                print(f"📄 {endpoint.upper()}: {endpoint_success}/{endpoint_total} tests passed ({success_rate:.1f}%)")
        
        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 OVERALL: {successful_tests}/{total_tests} tests passed ({overall_success_rate:.1f}%)")
        
        if overall_success_rate == 100:
            print("🎉 All tests passed! The Moondream API integration is working perfectly.")
        elif overall_success_rate >= 75:
            print("✅ Most tests passed. Minor issues may need attention.")
        elif overall_success_rate >= 50:
            print("⚠️  Some tests failed. Check API configuration and connectivity.")
        else:
            print("❌ Many tests failed. Check API server, credentials, and network connectivity.")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

def find_test_image() -> Path:
    """
    Find a suitable test image in common locations
    
    Returns:
        Path to a test image file
        
    Raises:
        FileNotFoundError: If no suitable test image is found
    """
    # Try direct file paths first
    direct_paths = [
        Path("test_image.jpg"),
        Path("test_image.png"),
        Path("captured_frame.jpg"),
    ]
    
    for path in direct_paths:
        if path.exists():
            return path
    
    # Try glob patterns
    glob_patterns = [
        Path("static/images").glob("*.jpg"),
        Path("static/images").glob("*.png"),
        Path(".").glob("*.jpg"),
        Path(".").glob("*.png")
    ]
    
    for pattern in glob_patterns:
        try:
            for file_path in pattern:
                if file_path.exists():
                    return file_path
        except (TypeError, AttributeError):
            continue
    
    raise FileNotFoundError(
        "No test image found. Please provide an image file path as an argument, "
        "or place a test image (test_image.jpg/png) in the current directory."
    )

async def main():
    """Main test execution function"""
    # Get image path from command line or find default
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
    else:
        try:
            image_path = find_test_image()
            print(f"📷 Using default test image: {image_path}")
        except FileNotFoundError as e:
            print(f"❌ {str(e)}")
            return
    
    # Create tester and run tests
    tester = MoondreamTester()
    
    try:
        results = await tester.run_full_test_suite(image_path)
        
        # Save results to file
        results_file = Path("moondream_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Full test results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
    
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main()) 