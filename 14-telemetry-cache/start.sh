#!/bin/bash

# Telemetry Cache Service Startup Script

echo "Starting Telemetry Cache Service..."

# Set environment variables
export TELEMETRY_CACHE_VERSION="1.0.0"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Change to the script directory
cd "$(dirname "$0")"

# Check if Redis is available
if ! python3 -c "import redis; r = redis.Redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; then
    echo "Warning: Redis not available at $REDIS_URL"
    echo "Starting without Redis caching..."
fi

# Start the service
echo "Starting FastAPI server on port 8000..."
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
