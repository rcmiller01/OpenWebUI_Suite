#!/usr/bin/env python3
"""
Test the emotion templates functionality in the feeling engine
"""

import json
import requests
import time

def test_emotion_templates():
    """Test the emotion templates endpoint"""
    base_url = "http://localhost:8103"
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test get templates endpoint
    print("\nTesting templates endpoint...")
    try:
        response = requests.get(f"{base_url}/templates", timeout=5)
        if response.status_code == 200:
            templates = response.json()
            print(f"Templates loaded: {templates['count']}")
            for template in templates['templates']:
                print(f"  - {template['id']}: {template['label']}")
        else:
            print(f"Templates endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"Templates test failed: {e}")
    
    # Test augment endpoint with different templates
    print("\nTesting augment endpoint...")
    test_prompt = "You are a helpful AI assistant. Answer the user's question clearly and concisely."
    
    test_cases = [
        ("none", "No emotional augmentation"),
        ("stakes", "High-stakes diligence"),
        ("self_monitor", "Self-monitor + verify"),
        ("standards", "Professional standard"),
        ("empathy_therapist", "Therapeutic empathy")
    ]
    
    for template_id, template_name in test_cases:
        try:
            payload = {
                "system_prompt": test_prompt,
                "emotion_template_id": template_id
            }
            response = requests.post(f"{base_url}/augment", json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ {template_name} ({template_id}):")
                print(f"Applied template: {result['template_label']}")
                print(f"Augmented prompt length: {len(result['system_prompt'])} chars")
                print("Augmented prompt:")
                print("-" * 50)
                print(result['system_prompt'])
                print("-" * 50)
            else:
                print(f"❌ {template_name} failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ {template_name} test failed: {e}")

if __name__ == "__main__":
    print("Testing Feeling Engine Emotion Templates")
    print("=" * 50)
    test_emotion_templates()
