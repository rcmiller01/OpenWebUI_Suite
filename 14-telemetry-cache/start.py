#!/usr/bin/env python3
"""
Telemetry Cache Service - Python Startup Script
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main startup function"""

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Telemetry Cache Service v1.0.0")

    # Set environment variables
    os.environ.setdefault("TELEMETRY_CACHE_VERSION", "1.0.0")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("PROMETHEUS_PORT", "9090")

    # Check Redis connectivity
    try:
        import redis  # type: ignore
        redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    # Start server
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
