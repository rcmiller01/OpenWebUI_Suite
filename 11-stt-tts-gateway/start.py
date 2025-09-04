#!/usr/bin/env python3
"""
Startup script for STT-TTS Gateway service
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="STT-TTS Gateway Service")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to"
    )
    parser.add_argument(
        "--port", type=int, default=8089, help="Port to bind to"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload"
    )
    parser.add_argument(
        "--log-level", default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Set environment variables
    os.environ.setdefault("AUDIO_STORAGE_PATH", "./audio")

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Starting STT-TTS Gateway on {args.host}:{args.port}")

    # Import and run the app
    try:
        from app import app
        import uvicorn

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except ImportError as e:
        logger.error(f"Failed to import application: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
