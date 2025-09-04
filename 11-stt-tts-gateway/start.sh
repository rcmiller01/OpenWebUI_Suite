#!/bin/bash
# Startup script for STT-TTS Gateway service

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set default environment variables
export AUDIO_STORAGE_PATH="${AUDIO_STORAGE_PATH:-./audio}"
export STT_MODEL_SIZE="${STT_MODEL_SIZE:-base}"
export TTS_MODEL_NAME="${TTS_MODEL_NAME:-tts_models/en/ljspeech/tacotron2-DDC_ph}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000,http://localhost:8080}"

# Create audio storage directory
mkdir -p "$AUDIO_STORAGE_PATH"

echo "Starting STT-TTS Gateway Service..."
echo "Audio storage: $AUDIO_STORAGE_PATH"
echo "STT model: $STT_MODEL_SIZE"
echo "TTS model: $TTS_MODEL_NAME"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the service
exec python start.py "$@"
