#!/usr/bin/env python3
"""
Startup script for Hidden Multi-Expert Merger Service
"""

import uvicorn
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import app

if __name__ == "__main__":
    print("Starting Hidden Multi-Expert Merger Service on port 8104...")
    uvicorn.run(app, host="0.0.0.0", port=8104)
