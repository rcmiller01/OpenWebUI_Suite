#!/bin/bash

# Policy Guardrails Service Startup Script

echo "Starting Policy Guardrails Service..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
echo "Starting FastAPI server on port 8113..."
uvicorn src.app:app --host 0.0.0.0 --port 8113 --reload
