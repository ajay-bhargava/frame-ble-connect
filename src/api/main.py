from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

from src.api.routes import analysis, device, parking, haptic

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Frame Glasses AI API",
    description="AI-powered vision analysis API for Frame glasses with haptic-triggered capture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print(f"📁 Static files mounted at /static")

# Include routers
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(device.router, prefix="/api/v1")
app.include_router(parking.router, prefix="/api/v1")
app.include_router(haptic.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Frame Glasses AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analysis": "/api/v1/analysis",
            "device": "/api/v1/device",
            "parking": "/api/v1/parking",
            "haptic": "/api/v1/haptic"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Frame Glasses AI API"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )

def start_server():
    """Start the FastAPI server with configuration"""
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
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    start_server() 