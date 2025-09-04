#!/usr/bin/env python3
"""
Quick test of the Drive State API
"""

import sys
import os
import subprocess
import time
import requests

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from drive_state import drive_manager


def test_server():
    """Test the server by starting it and making a request"""
    print("Testing server functionality...")

    # Test direct API first
    print("1. Testing direct drive manager...")
    state = drive_manager.get_drive_state("test_user")
    print(f"   ✅ Got drive state - Energy: {state.energy:.2f}")

    # Test update
    updated = drive_manager.update_drive_state("test_user", {"energy": 0.2}, "Test update")
    print(f"   ✅ Updated drive state - Energy: {updated.energy:.2f}")

    # Test policy
    policy = drive_manager.get_style_policy("test_user")
    print(f"   ✅ Got style policy - Energy level: {policy['energy_level']}")

    # Start server
    print("2. Starting server...")
    server_process = subprocess.Popen([
        sys.executable, 'start.py'
    ], cwd=os.path.dirname(__file__))

    # Wait for server to start
    time.sleep(2)

    try:
        # Test health endpoint
        print("3. Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8105/health", timeout=5)
        print(f"   ✅ Health check: {response.status_code}")

        # Test get drive state
        print("4. Testing get drive state...")
        response = requests.get("http://127.0.0.1:8105/drive/get?user_id=test_user", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Get state: Energy {data['energy']:.2f}")
        else:
            print(f"   ❌ Get state failed: {response.status_code}")

        # Test update drive state
        print("5. Testing update drive state...")
        payload = {
            "delta": {"sociability": 0.3},
            "reason": "Made new friend"
        }
        response = requests.post(
            "http://127.0.0.1:8105/drive/update?user_id=test_user",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Update state: Sociability {data['sociability']:.2f}")
        else:
            print(f"   ❌ Update state failed: {response.status_code}")

        # Test style policy
        print("6. Testing style policy...")
        response = requests.post("http://127.0.0.1:8105/drive/policy?user_id=test_user", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Style policy: {len(data['style_hints'])} hints")
        else:
            print(f"   ❌ Style policy failed: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    finally:
        # Clean up server
        print("7. Shutting down server...")
        server_process.terminate()
        server_process.wait(timeout=5)

    print("✅ Server test completed")


if __name__ == "__main__":
    test_server()
