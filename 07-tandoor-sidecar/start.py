#!/usr/bin/env python3
"""
Tandoor Sidecar - Startup Script
Starts the Tandoor Sidecar service on port 8107
"""

import sys
import os
import uvicorn

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("Starting Tandoor Sidecar on port 8107...")
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8107,
        reload=True,
        log_level="info"
    )
