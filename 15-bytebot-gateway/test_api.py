#!/usr/bin/env python3
"""
Test script for the ByteBot Gateway API
"""

import requests
import json
import time
import hmac
import hashlib
import base64

BASE_URL = "http://127.0.0.1:8089"
SHARED_SECRET = "test-secret-key-change-in-production"

def generate_signature(payload: str, timestamp: str) -> str:
    """Generate HMAC signature for request authentication"""
    message = f"{timestamp}:{payload}"
    signature = hmac.new(
        SHARED_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_capabilities():
    """Test the capabilities endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/capabilities")
        print(f"Capabilities - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Capabilities test failed: {e}")
        return False

def test_plan_endpoint():
    """Test the plan endpoint with HMAC signature"""
    payload = {
        "action": "fs.read",
        "parameters": {
            "path": "/tmp/test.txt"
        }
    }

    payload_str = json.dumps(payload, separators=(',', ':'))
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(payload_str, timestamp)

    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-Signature": signature
    }

    try:
        response = requests.post(
            f"{BASE_URL}/plan",
            headers=headers,
            json=payload
        )
        print(f"Plan Endpoint - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Plan endpoint test failed: {e}")
        return False

def test_execute_endpoint():
    """Test the execute endpoint with HMAC signature"""
    payload = {
        "task_id": "test-task-123",
        "action": "fs.read",
        "parameters": {
            "path": "/tmp/test.txt"
        }
    }

    payload_str = json.dumps(payload, separators=(',', ':'))
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(payload_str, timestamp)

    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-Signature": signature
    }

    try:
        response = requests.post(
            f"{BASE_URL}/execute",
            headers=headers,
            json=payload
        )
        print(f"Execute Endpoint - Status: {response.status_code}")
        if response.status_code in [200, 202]:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Execute endpoint test failed: {e}")
        return False

def test_events_endpoint():
    """Test the events endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/events")
        print(f"Events Endpoint - Status: {response.status_code}")
        if response.status_code == 200:
            print("Events stream connected successfully")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Events endpoint test failed: {e}")
        return False

def test_invalid_signature():
    """Test with invalid HMAC signature"""
    payload = {
        "action": "fs.read",
        "parameters": {
            "path": "/tmp/test.txt"
        }
    }

    timestamp = str(int(time.time() * 1000))
    signature = "invalid-signature"

    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-Signature": signature
    }

    try:
        response = requests.post(
            f"{BASE_URL}/plan",
            headers=headers,
            json=payload
        )
        print(f"Invalid Signature Test - Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly rejected invalid signature")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}: "
                  f"{response.text}")
            return False
    except Exception as e:
        print(f"Invalid signature test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔄 Starting API Tests for ByteBot Gateway\n")

    # Test 1: Health Check
    print("1️⃣ Testing Health Endpoint")
    health_ok = test_health()
    print()

    if not health_ok:
        print("❌ Health check failed. Server might not be running.")
        return

    # Test 2: Capabilities
    print("2️⃣ Testing Capabilities Endpoint")
    capabilities_ok = test_capabilities()
    print()

    # Test 3: Plan Endpoint
    print("3️⃣ Testing Plan Endpoint")
    plan_ok = test_plan_endpoint()
    print()

    # Test 4: Execute Endpoint
    print("4️⃣ Testing Execute Endpoint")
    execute_ok = test_execute_endpoint()
    print()

    # Test 5: Events Endpoint
    print("5️⃣ Testing Events Endpoint")
    events_ok = test_events_endpoint()
    print()

    # Test 6: Invalid Signature
    print("6️⃣ Testing Invalid Signature Rejection")
    invalid_sig_ok = test_invalid_signature()
    print()

    # Summary
    print("📊 Test Summary:")
    print(f"   Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Capabilities: {'✅ PASS' if capabilities_ok else '❌ FAIL'}")
    print(f"   Plan Endpoint: {'✅ PASS' if plan_ok else '❌ FAIL'}")
    print(f"   Execute Endpoint: {'✅ PASS' if execute_ok else '❌ FAIL'}")
    print(f"   Events Endpoint: {'✅ PASS' if events_ok else '❌ FAIL'}")
    print(f"   Invalid Signature: {'✅ PASS' if invalid_sig_ok else '❌ FAIL'}")

    all_passed = all([health_ok, capabilities_ok, plan_ok,
                      execute_ok, events_ok, invalid_sig_ok])
    if all_passed:
        print("\n🎉 All tests passed! The ByteBot Gateway is working "
              "correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
