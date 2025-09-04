#!/usr/bin/env python3
"""
Startup script for ByteBot Gateway
"""

import sys
import os
import subprocess

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def main():
    """Start the ByteBot Gateway service"""
    print("🚀 Starting ByteBot Gateway...")

    try:
        # Change to the script directory
        os.chdir(current_dir)

        # Start uvicorn with the correct module path
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.app:app",
            "--host", "0.0.0.0",
            "--port", "8089",
            "--reload"
        ]

        print(f"Running: {' '.join(cmd)}")
        print(f"Directory: {os.getcwd()}")

        subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        print("\n🛑 ByteBot Gateway stopped by user")
    except Exception as e:
        print(f"❌ Error starting ByteBot Gateway: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
