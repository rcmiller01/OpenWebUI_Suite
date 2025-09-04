#!/usr/bin/env python3
"""
Quick test of the Hidden Multi-Expert Merger API
"""

import sys
import os
import asyncio
import requests
import subprocess
import time
import signal

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import merger


def test_server():
    """Test the server by starting it and making a request"""
    print("Testing server functionality...")

    # Test direct API first
    print("1. Testing direct merger...")
    result = asyncio.run(merger.compose(
        "Write a professional email",
        "Project Manager",
        ["professional"],
        {"time_ms": 1000}
    ))

    print(f"   ✅ Direct test: {result['processing_time_ms']:.1f}ms, {result['helpers_used']} helpers")

    # Test server startup
    print("2. Starting server...")
    server_process = subprocess.Popen([
        sys.executable, 'start.py'
    ], cwd=os.path.dirname(__file__))

    # Wait for server to start
    time.sleep(2)

    try:
        # Test health endpoint
        print("3. Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8104/health", timeout=5)
        print(f"   ✅ Health check: {response.status_code}")

        # Test compose endpoint
        print("4. Testing compose endpoint...")
        payload = {
            "prompt": "Write a product description",
            "persona": "Marketing Specialist",
            "tone_policy": ["engaging"]
        }
        response = requests.post(
            "http://127.0.0.1:8104/compose",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Compose API: {data['processing_time_ms']:.1f}ms")
            print(f"   📝 Result: {data['final_text'][:80]}...")
        else:
            print(f"   ❌ Compose API failed: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    finally:
        # Clean up server
        print("5. Shutting down server...")
        server_process.terminate()
        server_process.wait(timeout=5)

    print("✅ Server test completed")


if __name__ == "__main__":
    test_server()
