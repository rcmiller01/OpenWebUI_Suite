#!/usr/bin/env python3
"""
Test script for Memory 2.0 API
"""

import requests
import json

BASE_URL = "http://localhost:8102"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_store_memory():
    """Test storing a memory candidate"""
    data = {
        "content": "I am a software engineer and I love Python programming. I work at Microsoft.",
        "user_id": "test_user_123"
    }
    
    response = requests.post(f"{BASE_URL}/mem/candidates", json=data)
    print(f"Store memory: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_retrieve_memories():
    """Test retrieving memories"""
    params = {
        "user_id": "test_user_123",
        "limit": 5
    }
    
    response = requests.get(f"{BASE_URL}/mem/retrieve", params=params)
    print(f"Retrieve memories: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_memory_summary():
    """Test memory summary"""
    params = {"user_id": "test_user_123"}
    
    response = requests.get(f"{BASE_URL}/mem/summary", params=params)
    print(f"Memory summary: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def main():
    """Run all tests"""
    print("🧠 Testing Memory 2.0 API...\n")
    
    try:
        test_health()
        test_store_memory()
        test_retrieve_memories()
        test_memory_summary()
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Memory 2.0 service. Is it running on port 8102?")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
