#!/bin/bash
# start.sh - Development startup script for ByteBot Gateway

set -e

echo "🚀 Starting ByteBot Gateway..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set default environment variables if not set
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8089}

echo "📋 Configuration:"
echo "  - Host: $HOST"
echo "  - Port: $PORT"
echo "  - Log Level: $LOG_LEVEL"
echo "  - ByteBot URL: ${BYTEBOT_URL:-http://localhost:3000}"

# Start the server
echo "🌟 Starting server at http://$HOST:$PORT"
echo "📚 API Documentation: http://$HOST:$PORT/docs"
echo "💓 Health Check: http://$HOST:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn src.app:app --reload --host $HOST --port $PORT
