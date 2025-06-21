#!/usr/bin/env python3
"""
Startup script for Frame Glasses AI API
"""
import sys
import os
import uvicorn
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("🚀 Starting Frame Glasses AI API")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {reload}")
    print("-" * 50)
    
    # Check for required environment variables
    if not os.getenv("MOONDREAM_API_KEY"):
        print("⚠️  Warning: MOONDREAM_API_KEY not set")
        print("   Set it in your .env file or environment")
    
    # Start the server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 