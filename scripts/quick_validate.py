#!/usr/bin/env python3
"""
Quick deployment validation for OpenWebUI Suite
Run this after docker-compose up to verify core functionality
"""

import requests
import sys
import time


def validate_core_services():
    """Validate the 4 most critical services"""
    critical_services = [
        ("Gateway", "http://localhost:8000/healthz"),
        ("Intent Router", "http://localhost:8101/healthz"),
        ("Memory", "http://localhost:8102/healthz"),
        ("Feeling Engine", "http://localhost:8103/healthz"),
    ]
    
    print("🚀 Validating OpenWebUI Suite Deployment")
    print("=" * 50)
    
    all_healthy = True
    
    for service, url in critical_services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service:15} - Healthy")
            else:
                print(f"❌ {service:15} - HTTP {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"❌ {service:15} - {str(e)}")
            all_healthy = False
    
    # Test enhanced routing
    print(f"\n🧠 Testing Enhanced Routing")
    print("-" * 50)
    
    test_cases = [
        ("TECH query", "How do I fix this Python error?", "TECH"),
        ("PSYCHOTHERAPY", "I'm feeling anxious", "PSYCHOTHERAPY"),
        ("LEGAL query", "What are the GDPR requirements?", "LEGAL"),
    ]
    
    routing_works = True
    for name, query, expected_family in test_cases:
        try:
            response = requests.post("http://localhost:8101/route", 
                                   json={"user_text": query}, timeout=5)
            if response.status_code == 200:
                result = response.json()
                family = result.get("family", "UNKNOWN")
                if family == expected_family:
                    print(f"✅ {name:15} - Routed to {family}")
                else:
                    print(f"⚠️  {name:15} - Expected {expected_family}, got {family}")
            else:
                print(f"❌ {name:15} - HTTP {response.status_code}")
                routing_works = False
        except Exception as e:
            print(f"❌ {name:15} - {str(e)}")
            routing_works = False
    
    print(f"\n📊 Summary")
    print("-" * 50)
    
    if all_healthy and routing_works:
        print("🟢 Deployment Status: SUCCESS")
        print("✨ Your OpenWebUI Suite is ready!")
        return 0
    elif all_healthy:
        print("🟡 Deployment Status: PARTIAL")
        print("⚠️  Core services healthy, routing needs attention")
        return 1
    else:
        print("🔴 Deployment Status: FAILED")
        print("❌ Critical services are not healthy")
        return 2


if __name__ == "__main__":
    sys.exit(validate_core_services())
