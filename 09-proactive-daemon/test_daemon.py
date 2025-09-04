#!/usr/bin/env python3
"""
Test script for Proactive Daemon

Tests the worker functionality with dry-run mode and mock data.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from worker import ProactiveDaemon


async def test_dry_run():
    """Test dry run functionality"""
    print("Testing Proactive Daemon in dry-run mode...")

    config_path = Path(__file__).parent / 'config' / 'triggers.yaml'

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    # Initialize daemon in dry-run mode
    daemon = ProactiveDaemon(str(config_path), dry_run=True)

    try:
        # Run all trigger checks
        await daemon.run_once()
        print("✅ Dry run test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Dry run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config_loading():
    """Test configuration loading"""
    print("Testing configuration loading...")

    config_path = Path(__file__).parent / 'config' / 'triggers.yaml'

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    try:
        daemon = ProactiveDaemon(str(config_path), dry_run=True)
        print("✅ Configuration loaded successfully")
        print(f"   Pipelines URL: {daemon.config['global']['pipelines_url']}")
        print(f"   Dry run: {daemon.config['global']['dry_run']}")
        return True

    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


async def test_idempotency():
    """Test idempotency functionality"""
    print("Testing idempotency functionality...")

    config_path = Path(__file__).parent / 'config' / 'triggers.yaml'

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    try:
        daemon = ProactiveDaemon(str(config_path), dry_run=True)

        # Test duplicate detection
        key = "test_key_123"
        trigger_type = "test_trigger"

        # First call should not be duplicate
        is_dup1 = daemon.idempotency.is_duplicate(key, trigger_type)
        print(f"   First call duplicate: {is_dup1}")

        # Second call should be duplicate
        is_dup2 = daemon.idempotency.is_duplicate(key, trigger_type)
        print(f"   Second call duplicate: {is_dup2}")

        if not is_dup1 and is_dup2:
            print("✅ Idempotency test passed")
            return True
        else:
            print("❌ Idempotency test failed")
            return False

    except Exception as e:
        print(f"❌ Idempotency test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("Running Proactive Daemon Tests...\n")

    tests = [
        test_config_loading,
        test_idempotency,
        test_dry_run
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if await test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
