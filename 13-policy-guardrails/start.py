#!/usr/bin/env python3
"""
Policy Guardrails Service - Python Startup Script
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    logger.info("Starting Policy Guardrails Service...")

    # Add src directory to Python path
    src_path = os.path.join(os.path.dirname(__file__), "src")
    sys.path.insert(0, src_path)

    # Check if virtual environment should be used
    venv_path = os.path.join(os.path.dirname(__file__), "venv")
    if os.path.exists(venv_path):
        logger.info("Virtual environment found")
        if sys.platform == "win32":
            python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(venv_path, "bin", "python")
    else:
        python_exe = sys.executable

    # Install dependencies if needed
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_file):
        logger.info("Installing dependencies...")
        try:
            subprocess.check_call([
                python_exe, "-m", "pip", "install", "-r", requirements_file
            ])
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return 1

    # Start uvicorn server
    logger.info("Starting FastAPI server on port 8113...")
    try:
        subprocess.run([
            python_exe, "-m", "uvicorn",
            "src.app:app",
            "--host", "0.0.0.0",
            "--port", "8113",
            "--reload"
        ])
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
