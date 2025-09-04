#!/usr/bin/env python3
"""
Test script for Feeling Engine API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8103"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_analyze_positive():
    """Test affect analysis with positive text"""
    data = {
        "text": "I am so happy and excited about this amazing opportunity! It's wonderful and fantastic."
    }

    response = requests.post(f"{BASE_URL}/affect/analyze", json=data)
    print(f"Analyze positive text: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_analyze_negative():
    """Test affect analysis with negative text (sad text as specified)"""
    data = {
        "text": "I feel so sad and depressed. Everything is terrible and I'm really upset about this."
    }

    response = requests.post(f"{BASE_URL}/affect/analyze", json=data)
    print(f"Analyze negative/sad text: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    # Verify the test case: Sad text → {sentiment:neg, emotions:[sad]}
    if result.get('sentiment') == 'negative' and 'sadness' in result.get('emotions', []):
        print("✅ Test case PASSED: Sad text correctly identified as negative with sadness emotion")
    else:
        print("❌ Test case FAILED: Expected negative sentiment with sadness emotion")
    print()

def test_analyze_question():
    """Test affect analysis with question"""
    data = {
        "text": "What time is the meeting? Can you help me with this?"
    }

    response = requests.post(f"{BASE_URL}/affect/analyze", json=data)
    print(f"Analyze question: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_tone_policy():
    """Test tone policy generation"""
    data = {
        "text": "We need to discuss the quarterly results and strategic planning for next year.",
        "target_audience": "executive"
    }

    response = requests.post(f"{BASE_URL}/affect/tone", json=data)
    print(f"Tone policy generation: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_critique_short():
    """Test text critique with short text"""
    data = {
        "text": "This is a simple test message.",
        "max_tokens": 10
    }

    response = requests.post(f"{BASE_URL}/affect/critique", json=data)
    print(f"Critique short text: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_critique_long():
    """Test text critique with long rambling text"""
    long_text = """
    Um, so basically, I was thinking, you know, that we should, like, do something about this.
    It's really, really important, you know, and we need to, um, address it soon.
    Basically, the issue is that, you know, things are not working properly and we need to fix them.
    It's really frustrating, actually, and we should do something about it immediately.
    """

    data = {
        "text": long_text,
        "max_tokens": 20
    }

    response = requests.post(f"{BASE_URL}/affect/critique", json=data)
    print(f"Critique long rambling text: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    # Verify the test case: Critique removes ramble > N tokens
    if result.get('cleaned_tokens', 0) <= 20 and result.get('changes_made'):
        print("✅ Test case PASSED: Long text critiqued and truncated to max tokens")
    else:
        print("❌ Test case FAILED: Text not properly critiqued")
    print()

def test_performance():
    """Test performance - should be < 50ms per call"""
    data = {
        "text": "This is a test message for performance analysis."
    }

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/affect/analyze", json=data)
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000
    print(f"Performance test: {response.status_code}")
    print(".2f")

    if latency_ms < 50:
        print("✅ Performance test PASSED: Latency < 50ms")
    else:
        print("❌ Performance test FAILED: Latency >= 50ms")
    print()

def main():
    """Run all tests"""
    print("🎭 Testing Feeling Engine API...\n")

    try:
        test_health()
        test_analyze_positive()
        test_analyze_negative()  # Key test case
        test_analyze_question()
        test_tone_policy()
        test_critique_short()
        test_critique_long()  # Key test case
        test_performance()

        print("✅ All tests completed!")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Feeling Engine service. Is it running on port 8103?")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
