#!/usr/bin/env python3
"""
Test the enhanced intent router with family classification and emotion templates
"""

import requests
import json

def test_intent_router():
    """Test the new /route endpoint"""
    base_url = "http://localhost:8101"
    
    # Test cases covering different content families
    test_cases = [
        {
            "text": "How do I fix this Python error: TypeError: list indices must be integers",
            "expected_family": "TECH",
            "expected_template": "none",
            "expected_provider": "openrouter"
        },
        {
            "text": "I need help with my contract terms and GDPR compliance",
            "expected_family": "LEGAL", 
            "expected_template": "none",
            "expected_provider": "openrouter"
        },
        {
            "text": "I'm feeling really anxious about my therapy session tomorrow",
            "expected_family": "PSYCHOTHERAPY",
            "expected_template": "empathy_therapist",
            "expected_provider": "openrouter"
        },
        {
            "text": "Please prove that the sum of two even numbers is always even",
            "expected_family": "GENERAL_PRECISION",
            "expected_template": "self_monitor",
            "expected_provider": "local"
        },
        {
            "text": "What's your favorite color and why?",
            "expected_family": "OPEN_ENDED",
            "expected_template": "stakes",
            "expected_provider": "local"
        },
        {
            "text": "We need SOX compliance for our financial data processing",
            "expected_family": "REGULATED",
            "expected_template": "none",
            "expected_provider": "local"  # default local for regulated
        }
    ]
    
    print("Testing Intent Router Family Classification")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['expected_family']}")
        print(f"Input: {test_case['text'][:60]}...")
        
        try:
            # Test the new /route endpoint
            response = requests.post(
                f"{base_url}/route",
                json={"user_text": test_case["text"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Family: {result['family']} (expected: {test_case['expected_family']})")
                print(f"✅ Template: {result['emotion_template_id']} (expected: {test_case['expected_template']})")
                print(f"✅ Provider: {result['provider']} (expected: {test_case['expected_provider']})")
                print(f"✅ Models: {result['openrouter_model_priority'][:2]}...")  # Show first 2 models
                print(f"✅ Tags: {result['tags']}")
                
                # Verify expectations
                assert result['family'] == test_case['expected_family'], f"Family mismatch: got {result['family']}, expected {test_case['expected_family']}"
                assert result['emotion_template_id'] == test_case['expected_template'], f"Template mismatch: got {result['emotion_template_id']}, expected {test_case['expected_template']}"
                assert result['provider'] == test_case['expected_provider'], f"Provider mismatch: got {result['provider']}, expected {test_case['expected_provider']}"
                
            else:
                print(f"❌ Route endpoint failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

def test_feeling_engine():
    """Test the emotion templates in feeling engine"""
    base_url = "http://localhost:8103"
    
    print("\n\nTesting Feeling Engine Emotion Templates")
    print("=" * 50)
    
    test_prompt = "You are a helpful AI assistant. Answer the user's question."
    
    templates_to_test = [
        "none",
        "stakes", 
        "self_monitor",
        "standards",
        "empathy_therapist"
    ]
    
    for template_id in templates_to_test:
        try:
            response = requests.post(
                f"{base_url}/augment",
                json={
                    "system_prompt": test_prompt,
                    "emotion_template_id": template_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Template: {template_id}")
                print(f"   Label: {result['template_label']}")
                print(f"   Length: {len(result['system_prompt'])} chars")
                print(f"   Augmented: {'Yes' if len(result['system_prompt']) > len(test_prompt) else 'No'}")
            else:
                print(f"❌ Template {template_id} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Template {template_id} error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Enhanced Intent Router and Feeling Engine")
    print("=" * 60)
    
    # Test health endpoints first
    for service, port in [("intent", 8101), ("feeling", 8103)]:
        try:
            response = requests.get(f"http://localhost:{port}/healthz", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service.title()} service healthy")
            else:
                print(f"❌ {service.title()} service unhealthy: {response.status_code}")
        except Exception as e:
            print(f"❌ {service.title()} service unreachable: {e}")
    
    test_intent_router()
    test_feeling_engine()
    
    print("\n🎉 Testing completed!")
