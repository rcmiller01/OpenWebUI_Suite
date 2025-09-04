#!/usr/bin/env python3
"""
Start script for Proactive Daemon (Python version for cross-platform compatibility)
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point"""
    # Set default configuration
    config_file = os.getenv('CONFIG_FILE', 'config/triggers.yaml')
    worker_args = []

    # Check if config file exists
    if not Path(config_file).exists():
        print(f"Error: Configuration file not found: {config_file}")
        print("Please create config/triggers.yaml or set CONFIG_FILE environment variable")
        sys.exit(1)

    worker_args.extend(['--config', config_file])

    # Add dry-run flag if DRY_RUN is set
    if os.getenv('DRY_RUN', 'false').lower() == 'true':
        worker_args.append('--dry-run')

    # Add verbose flag if VERBOSE is set
    if os.getenv('VERBOSE', 'false').lower() == 'true':
        worker_args.append('--verbose')

    # Add once flag if ONCE is set
    if os.getenv('ONCE', 'false').lower() == 'true':
        worker_args.append('--once')

    print("Starting Proactive Daemon...")
    print(f"Config: {config_file}")
    print(f"Args: {' '.join(worker_args)}")

    # Run the worker
    cmd = [sys.executable, 'src/worker.py'] + worker_args
    result = subprocess.run(cmd)

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
