#!/usr/bin/env python3
"""
BYOF Tool Hub - Startup Script
Starts the BYOF Tool Hub service on port 8106
"""

import sys
import os
import uvicorn

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("Starting BYOF Tool Hub on port 8106...")
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8106,
        reload=True,
        log_level="info"
    )
