#!/usr/bin/env python3
"""
Entry point for Frame Glasses AI API
Run with: python run.py
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and start the server
from api.main import start_server

if __name__ == "__main__":
    start_server() 