#!/usr/bin/env python3
"""
Startup script for Feeling Engine service
"""

import sys
import os
import subprocess

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def main():
    """Start the Feeling Engine service"""
    print("🎭 Starting Feeling Engine service...")

    try:
        # Change to the script directory
        os.chdir(current_dir)

        # Start uvicorn with the correct module path
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.app:app",
            "--host", "0.0.0.0",
            "--port", "8103",
            "--reload"
        ]

        print(f"Running: {' '.join(cmd)}")
        print(f"Directory: {os.getcwd()}")

        subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        print("\n🛑 Feeling Engine stopped by user")
    except Exception as e:
        print(f"❌ Error starting Feeling Engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
