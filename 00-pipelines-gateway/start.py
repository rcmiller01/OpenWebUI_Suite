#!/usr/bin/env python3
"""
Startup script for OpenWebUI Pipelines Gateway
"""

import sys
import os
import subprocess

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def main():
    """Start the Pipelines Gateway service"""
    print("🚀 Starting OpenWebUI Pipelines Gateway...")
    
    try:
        # Change to the script directory
        os.chdir(current_dir)
        
        # Start uvicorn with the correct module path
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.server:app",
            "--host", "0.0.0.0",
            "--port", "8088",
            "--reload"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print(f"Directory: {os.getcwd()}")
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Pipelines Gateway stopped by user")
    except Exception as e:
        print(f"❌ Error starting Pipelines Gateway: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
