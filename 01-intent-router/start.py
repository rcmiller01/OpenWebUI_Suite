#!/usr/bin/env python3
"""
Startup script for Intent Router service
"""

import sys
import os
import subprocess

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Start the Intent Router service"""
    print("🚀 Starting Intent Router service...")
    
    try:
        # Change to the script directory
        os.chdir(current_dir)
        
        # Start uvicorn with the correct module path
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "src.app:app", 
            "--host", "0.0.0.0",
            "--port", "8101",
            "--reload"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print(f"Directory: {os.getcwd()}")
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Intent Router stopped by user")
    except Exception as e:
        print(f"❌ Error starting Intent Router: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
