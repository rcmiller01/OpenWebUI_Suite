#!/usr/bin/env python3
"""
Test script for the OpenWebUI Pipelines Gateway API
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8088"

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

def test_chat_completion():
    """Test the chat completion endpoint"""
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello! Can you calculate 2 + 2 for me?"}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(f"Chat Completion - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Chat completion test failed: {e}")
        return False

def test_streaming():
    """Test the streaming chat completion endpoint"""
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5"}
        ],
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            stream=True
        )
        print(f"Streaming - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("Streaming chunks:")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = decoded_line[6:]  # Remove 'data: ' prefix
                        if data == '[DONE]':
                            print("Stream finished")
                            break
                        else:
                            try:
                                chunk = json.loads(data)
                                print(f"Chunk: {json.dumps(chunk, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"Invalid JSON: {data}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Streaming test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔄 Starting API Tests for OpenWebUI Pipelines Gateway\n")
    
    # Test 1: Health Check
    print("1️⃣ Testing Health Endpoint")
    health_ok = test_health()
    print()
    
    if not health_ok:
        print("❌ Health check failed. Server might not be running.")
        return
    
    # Test 2: Chat Completion
    print("2️⃣ Testing Chat Completion Endpoint")
    chat_ok = test_chat_completion()
    print()
    
    # Test 3: Streaming
    print("3️⃣ Testing Streaming Endpoint")
    stream_ok = test_streaming()
    print()
    
    # Summary
    print("📊 Test Summary:")
    print(f"   Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Chat Completion: {'✅ PASS' if chat_ok else '❌ FAIL'}")
    print(f"   Streaming: {'✅ PASS' if stream_ok else '❌ FAIL'}")
    
    if all([health_ok, chat_ok, stream_ok]):
        print("\n🎉 All tests passed! The Pipelines Gateway is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
