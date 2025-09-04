#!/bin/bash
# Start script for Proactive Daemon

# Set default configuration
CONFIG_FILE="${CONFIG_FILE:-config/triggers.yaml}"
WORKER_ARGS=""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    echo "Please create config/triggers.yaml or set CONFIG_FILE environment variable"
    exit 1
fi

# Add dry-run flag if DRY_RUN is set
if [ "${DRY_RUN:-false}" = "true" ]; then
    WORKER_ARGS="$WORKER_ARGS --dry-run"
fi

# Add verbose flag if VERBOSE is set
if [ "${VERBOSE:-false}" = "true" ]; then
    WORKER_ARGS="$WORKER_ARGS --verbose"
fi

# Add once flag if ONCE is set
if [ "${ONCE:-false}" = "true" ]; then
    WORKER_ARGS="$WORKER_ARGS --once"
fi

echo "Starting Proactive Daemon..."
echo "Config: $CONFIG_FILE"
echo "Args: $WORKER_ARGS"

# Run the worker
python src/worker.py --config "$CONFIG_FILE" $WORKER_ARGS
