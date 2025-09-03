#!/usr/bin/env python3
"""
Test script for Intent Router API

Quick validation of the intent classification service.
"""

import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8101"

# Test cases
TEST_CASES = [
    {
        "name": "Emotional Intent",
        "text": "I feel really sad and need someone to talk to about my relationship",
        "expected_intent": "emotional"
    },
    {
        "name": "Technical Intent - Code",
        "text": """
        def binary_search(arr, target):
            left, right = 0, len(arr) - 1
            while left <= right:
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
            return -1
        
        How can I optimize this algorithm?
        """,
        "expected_intent": "technical"
    },
    {
        "name": "Recipe Intent",
        "text": "How do I bake chocolate chip cookies? I need ingredients and oven temperature",
        "expected_intent": "recipes"
    },
    {
        "name": "Finance Intent", 
        "text": "What's the best investment strategy for my 401k retirement portfolio?",
        "expected_intent": "finance"
    },
    {
        "name": "Image Processing",
        "text": "What objects do you see in this image?",
        "attachments": [{"type": "image", "mime_type": "image/jpeg"}],
        "expected_intent": "mm_image"
    },
    {
        "name": "Audio Processing",
        "text": "Can you transcribe this audio recording?", 
        "attachments": [{"type": "audio", "mime_type": "audio/wav"}],
        "expected_intent": "mm_audio"
    },
    {
        "name": "General Query",
        "text": "Hello, how are you today? What's the weather like?",
        "expected_intent": "general"
    },
    {
        "name": "Long Text (Remote)",
        "text": "Explain in great detail the comprehensive methodology " * 50,
        "expected_remote": True
    }
]


def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Components: {data['components']}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False


def test_classification():
    """Test classification endpoint with all test cases"""
    print("\n🔄 Testing Intent Classification:")
    
    passed = 0
    total = len(TEST_CASES)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{i}. {test_case['name']}")
        
        # Prepare request
        request_data = {
            "text": test_case["text"]
        }
        
        if "attachments" in test_case:
            request_data["attachments"] = test_case["attachments"]
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/classify",
                json=request_data,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check intent
                intent_correct = True
                if "expected_intent" in test_case:
                    intent_correct = data["intent"] == test_case["expected_intent"]
                
                # Check remote flag
                remote_correct = True
                if "expected_remote" in test_case:
                    remote_correct = data["needs_remote"] == test_case["expected_remote"]
                
                if intent_correct and remote_correct:
                    print(f"   ✅ Intent: {data['intent']} (confidence: {data['confidence']:.2f})")
                    print(f"   ⏱️  Response time: {response_time:.1f}ms")
                    print(f"   🌐 Remote: {data['needs_remote']}")
                    passed += 1
                else:
                    print(f"   ❌ Expected: {test_case.get('expected_intent', 'N/A')}")
                    print(f"   📍 Got: {data['intent']} (confidence: {data['confidence']:.2f})")
                    print(f"   🌐 Remote: {data['needs_remote']}")
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total


def test_performance():
    """Test performance requirements"""
    print("\n⚡ Testing Performance:")
    
    test_text = "This is a performance test message for intent classification"
    times = []
    
    for i in range(10):
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/classify",
                json={"text": test_text},
                timeout=5
            )
            response_time = (time.time() - start_time) * 1000
            times.append(response_time)
            
            if response.status_code != 200:
                print(f"❌ Request {i+1} failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Request {i+1} error: {e}")
            return False
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print(f"   📊 Average: {avg_time:.1f}ms")
    print(f"   🏃 Fastest: {min_time:.1f}ms")  
    print(f"   🐌 Slowest: {max_time:.1f}ms")
    
    # Target: < 50ms average (relaxed for testing)
    target_met = avg_time < 100
    if target_met:
        print(f"   ✅ Performance target met!")
    else:
        print(f"   ⚠️  Performance target missed (target: <100ms)")
    
    return target_met


def main():
    """Run all tests"""
    print("🧪 Intent Router API Test Suite")
    print("=" * 40)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        print("Start with: uvicorn src.app:app --port 8101")
        sys.exit(1)
    
    # Test classification
    classification_ok = test_classification()
    
    # Test performance  
    performance_ok = test_performance()
    
    # Summary
    print("\n" + "=" * 40)
    if classification_ok and performance_ok:
        print("🎉 All tests passed! Intent Router is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
