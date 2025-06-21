#!/usr/bin/env python3
"""
Simple test script to verify API structure
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("Testing imports...")
        
        # Test API imports
        from api.models.requests import AnalysisType, CaptureRequest
        print("✅ API models imported successfully")
        
        from api.models.responses import AnalysisResult, FoodAnalysisResult
        print("✅ API response models imported successfully")
        
        from api.routes.analysis import router as analysis_router
        print("✅ Analysis routes imported successfully")
        
        from api.routes.device import router as device_router
        print("✅ Device routes imported successfully")
        
        from ai.processors.moondream_processor import MoondreamProcessor
        print("✅ Moondream processor imported successfully")
        
        # Test FastAPI app creation
        from api.main import app
        print("✅ FastAPI app imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_models():
    """Test Pydantic models"""
    try:
        print("\nTesting Pydantic models...")
        
        from api.models.requests import CaptureRequest
        from api.models.responses import DeviceStatus
        
        # Test request model
        capture_req = CaptureRequest(resolution=720, auto_exposure=True)
        print(f"✅ CaptureRequest: {capture_req}")
        
        # Test response model
        status = DeviceStatus(
            connected=True,
            battery_level=85,
            memory_usage="1024KB",
            last_capture=None
        )
        print(f"✅ DeviceStatus: {status}")
        
        print("🎉 All models working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Frame Glasses AI API Structure")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_models()
    
    if success:
        print("\n🎉 All tests passed! API structure is ready.")
        print("\nTo start the server:")
        print("1. Set your MOONDREAM_API_KEY in .env file")
        print("2. Run: source .venv/bin/activate && python start_api.py")
        print("3. Visit: http://localhost:8000/docs")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 