#!/usr/bin/env python3
"""
Startup script for Memory 2.0 service
"""

import sys
import os
import subprocess

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def main():
    """Start the Memory 2.0 service"""
    print("🧠 Starting Memory 2.0 service...")
    
    try:
        # Change to the script directory
        os.chdir(current_dir)
        
        # Start uvicorn with the correct module path
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.app:app",
            "--host", "0.0.0.0",
            "--port", "8102",
            "--reload"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print(f"Directory: {os.getcwd()}")
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Memory 2.0 stopped by user")
    except Exception as e:
        print(f"❌ Error starting Memory 2.0: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
