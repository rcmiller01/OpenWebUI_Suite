#!/usr/bin/env python3
"""
OpenWebUI Suite Sanity Check

Post-deployment smoke tests to verify all services are healthy and accessible.
Run this after deploying the suite to validate the system is working correctly.
"""

import requests
import time
import json
import os
import sys
from typing import Dict, List, Tuple

# Service configuration
SERVICES = {
    "gateway": {"port": 8000, "health": "/healthz", "test": "/health"},
    "intent": {"port": 8101, "health": "/healthz", "test": "/route"},
    "memory": {"port": 8102, "health": "/healthz", "test": "/healthz"},
    "feeling": {"port": 8103, "health": "/healthz", "test": "/templates"},
    "merger": {"port": 8104, "health": "/healthz", "test": "/healthz"},
    "drive": {"port": 8105, "health": "/healthz", "test": "/healthz"},
    "tools": {"port": 8106, "health": "/healthz", "test": "/healthz"},
    "tandoor": {"port": 8107, "health": "/healthz", "test": "/healthz"},
    "openbb": {"port": 8108, "health": "/healthz", "test": "/healthz"},
    "daemon": {"port": 8109, "health": "/healthz", "test": "/healthz"},
    "multimodal": {"port": 8110, "health": "/healthz", "test": "/healthz"},
    "stt-tts": {"port": 8111, "health": "/healthz", "test": "/healthz"},
    "avatar": {"port": 8112, "health": "/healthz", "test": "/healthz"},
    "policy": {"port": 8113, "health": "/healthz", "test": "/healthz"},
    "telemetry": {"port": 8114, "health": "/healthz", "test": "/metrics"},
    "fastvlm": {"port": 8115, "health": "/healthz", "test": "/healthz"},
}

BASE_URL = os.getenv("SUITE_BASE_URL", "http://localhost")
TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))


def check_service_health(service: str, config: Dict) -> Tuple[bool, str, float]:
    """Check if a service is healthy"""
    port = config["port"]
    health_path = config["health"]
    url = f"{BASE_URL}:{port}{health_path}"
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return True, "OK", response_time
        else:
            return False, f"HTTP {response.status_code}", response_time
            
    except requests.exceptions.ConnectionError:
        response_time = (time.time() - start_time) * 1000
        return False, "Connection refused", response_time
    except requests.exceptions.Timeout:
        response_time = (time.time() - start_time) * 1000
        return False, "Timeout", response_time
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return False, str(e), response_time


def test_service_functionality(service: str, config: Dict) -> Tuple[bool, str]:
    """Test basic functionality of a service"""
    port = config["port"]
    test_path = config["test"]
    url = f"{BASE_URL}:{port}{test_path}"
    
    try:
        if service == "intent":
            # Test intent router with sample input
            response = requests.post(url, json={
                "user_text": "How do I fix this Python error?",
                "tags": []
            }, timeout=TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                if "family" in result and "provider" in result:
                    return True, f"Classified as {result['family']}"
                else:
                    return False, "Invalid response format"
            else:
                return False, f"HTTP {response.status_code}"
                
        elif service == "feeling":
            # Test emotion templates endpoint
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                if "templates" in result and "count" in result:
                    return True, f"Loaded {result['count']} templates"
                else:
                    return False, "Invalid response format"
            else:
                return False, f"HTTP {response.status_code}"
                
        elif service == "telemetry":
            # Test metrics endpoint
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 200:
                # Check if it's Prometheus format
                content = response.text
                if "# HELP" in content or "# TYPE" in content:
                    return True, "Metrics available"
                else:
                    return False, "No metrics found"
            else:
                return False, f"HTTP {response.status_code}"
                
        else:
            # Generic health check
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 200:
                return True, "Functional"
            else:
                return False, f"HTTP {response.status_code}"
                
    except Exception as e:
        return False, str(e)


def check_integration() -> List[Tuple[str, bool, str]]:
    """Test service integrations"""
    tests = []
    
    # Test intent -> feeling integration
    try:
        # Get routing decision
        intent_response = requests.post(f"{BASE_URL}:8101/route", json={
            "user_text": "I'm feeling anxious about my presentation tomorrow"
        }, timeout=TIMEOUT)
        
        if intent_response.status_code == 200:
            route = intent_response.json()
            template_id = route.get("emotion_template_id")
            
            if template_id:
                # Test applying the template
                feeling_response = requests.post(f"{BASE_URL}:8103/augment", json={
                    "system_prompt": "You are a helpful assistant.",
                    "emotion_template_id": template_id
                }, timeout=TIMEOUT)
                
                if feeling_response.status_code == 200:
                    tests.append(("Intent → Feeling integration", True, "Working"))
                else:
                    tests.append(("Intent → Feeling integration", False, "Feeling API failed"))
            else:
                tests.append(("Intent → Feeling integration", False, "No template ID"))
        else:
            tests.append(("Intent → Feeling integration", False, "Intent API failed"))
            
    except Exception as e:
        tests.append(("Intent → Feeling integration", False, str(e)))
    
    # Test gateway projects (if enabled)
    try:
        projects_response = requests.get(f"{BASE_URL}:8000/api/v1/projects/", timeout=TIMEOUT)
        
        if projects_response.status_code == 200:
            tests.append(("Gateway projects", True, "Enabled and accessible"))
        elif projects_response.status_code == 404:
            tests.append(("Gateway projects", True, "Disabled (expected)"))
        else:
            tests.append(("Gateway projects", False, f"HTTP {projects_response.status_code}"))
            
    except Exception as e:
        tests.append(("Gateway projects", False, str(e)))
    
    return tests


def main():
    """Run comprehensive suite sanity check"""
    print("🔍 OpenWebUI Suite Sanity Check")
    print("=" * 60)
    
    total_services = len(SERVICES)
    healthy_services = 0
    functional_services = 0
    
    print(f"\n📡 Health Checks ({total_services} services)")
    print("-" * 60)
    
    for service, config in SERVICES.items():
        healthy, status, response_time = check_service_health(service, config)
        
        if healthy:
            healthy_services += 1
            print(f"✅ {service:12} - {status:20} ({response_time:6.1f}ms)")
        else:
            print(f"❌ {service:12} - {status:20} ({response_time:6.1f}ms)")
    
    print(f"\n🧪 Functionality Tests")
    print("-" * 60)
    
    for service, config in SERVICES.items():
        functional, result = test_service_functionality(service, config)
        
        if functional:
            functional_services += 1
            print(f"✅ {service:12} - {result}")
        else:
            print(f"❌ {service:12} - {result}")
    
    print(f"\n🔗 Integration Tests")
    print("-" * 60)
    
    integration_tests = check_integration()
    passed_integrations = 0
    
    for test_name, passed, result in integration_tests:
        if passed:
            passed_integrations += 1
            print(f"✅ {test_name} - {result}")
        else:
            print(f"❌ {test_name} - {result}")
    
    print(f"\n📊 Summary")
    print("-" * 60)
    print(f"Health:       {healthy_services:2}/{total_services} services healthy")
    print(f"Functionality: {functional_services:2}/{total_services} services functional")
    print(f"Integration:   {passed_integrations:2}/{len(integration_tests)} tests passed")
    
    # Calculate overall health
    health_percentage = (healthy_services / total_services) * 100
    functional_percentage = (functional_services / total_services) * 100
    integration_percentage = (passed_integrations / len(integration_tests)) * 100 if integration_tests else 100
    
    overall_score = (health_percentage + functional_percentage + integration_percentage) / 3
    
    print(f"\n🎯 Overall Health: {overall_score:.1f}%")
    
    if overall_score >= 90:
        print("🟢 System Status: EXCELLENT")
        exit_code = 0
    elif overall_score >= 75:
        print("🟡 System Status: GOOD")
        exit_code = 0
    elif overall_score >= 50:
        print("🟠 System Status: DEGRADED")
        exit_code = 1
    else:
        print("🔴 System Status: CRITICAL")
        exit_code = 2
    
    print("\n💡 Recommendations:")
    if healthy_services < total_services:
        print("   - Check Docker Compose logs for unhealthy services")
        print("   - Verify environment variables and configuration")
    if functional_services < healthy_services:
        print("   - Review service-specific configuration")
        print("   - Check for missing dependencies or API keys")
    if passed_integrations < len(integration_tests):
        print("   - Verify service-to-service communication")
        print("   - Check network configuration and service discovery")
    
    if exit_code == 0:
        print("   ✨ Your OpenWebUI Suite is ready for production!")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
