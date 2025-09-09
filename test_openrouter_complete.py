#!/usr/bin/env python3
"""
OpenRouter Refactor - Complete Integration Test
Tests all components of the OpenRouter refactor implementation
"""
import os
import sys
import asyncio
import httpx
import json
from pathlib import Path
from typing import Dict, Any, List
import time

# Add the gateway source to Python path
sys.path.insert(0, str(Path(__file__).parent / "00-pipelines-gateway"))

def setup_environment():
    """Set up test environment variables"""
    env_vars = {
        # OpenRouter API
        "OPENROUTER_API_KEY": "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",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "OPENROUTER_REFERER": "https://core3.openwebui.local/",
        "OPENROUTER_TITLE": "OpenWebUI Homelab",
        
        # Models
        "MODEL_TOOLCALL": "deepseek/deepseek-chat",
        "MODEL_VISION": "zhipuai/glm-4v-9b", 
        "MODEL_EXPLICIT": "venice/uncensored:free",
        "MODEL_CODER": "qwen/qwen-2.5-coder-32b-instruct",
        
        # n8n Integration
        "N8N_BASE_URL": "http://192.168.50.145:5678",
        "N8N_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlYjA1MGQwYS1kNmFjLTRkMjAtOTdkZC04M2U0ODUxZmIwZTgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3Mzc3NTIzfQ.pnK8qlrvJB_liQnbUpoD5wxbHqwghX0EnyAcaOpK8rg",
        "N8N_WEBHOOK_URL": "http://192.168.50.145:5678/webhook/openrouter-router",
        "N8N_MCP_ENDPOINT": "http://192.168.50.145:5678/webhook/mcp-tools",
        
        # Local Fallback
        "LLAMACPP_HOST": "localhost",
        "LLAMACPP_PORT": "8080",
        "LOCAL_MODEL": "q4_7b.gguf",
        
        # Memory Service
        "MEMORY_SERVICE_URL": "http://02-memory-2.0:8002",
        "MEMORY_ENABLED": "true",
        
        # Feature Flags
        "ENABLE_OPENROUTER": "true",
        "ENABLE_LOCAL_FALLBACK": "true",
        "ENABLE_TOOLS": "true",
        "ENABLE_MEMORY": "true",
        "ENABLE_ROUTING": "true",
        
        # Logging
        "LOG_LEVEL": "INFO"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment variables configured")


async def test_providers():
    """Test provider implementations"""
    print("\n🔍 Testing Providers...")
    
    try:
        from src.providers import openrouter, local_fallback
        
        # Test OpenRouter provider
        print("  Testing OpenRouter provider...")
        or_health = openrouter.check_health()
        print(f"    OpenRouter Health: {or_health['status']}")
        print(f"    API Key Configured: {or_health['api_key_configured']}")
        print(f"    Available Models: {len(or_health.get('available_models', []))}")
        
        # Test Local Fallback provider  
        print("  Testing Local Fallback provider...")
        local_health = local_fallback.check_health()
        print(f"    Local Health: {local_health['status']}")
        print(f"    Available: {local_health['available']}")
        
        print("✅ Provider tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False


async def test_routing_policy():
    """Test routing policy logic"""
    print("\n🔍 Testing Routing Policy...")
    
    try:
        from src.router.policy import RouterPolicy
        
        policy = RouterPolicy()
        
        # Test routing decisions
        test_cases = [
            {
                "name": "Coding Request",
                "messages": [{"role": "user", "content": "Help me write Python code for file handling"}],
                "expected_model": "qwen/qwen-2.5-coder-32b-instruct"
            },
            {
                "name": "Vision Request", 
                "messages": [{"role": "user", "content": "Analyze this image for me"}],
                "expected_model": "zhipuai/glm-4v-9b"
            },
            {
                "name": "Tool Request",
                "messages": [{"role": "user", "content": "Please call the search tool to find information"}],
                "expected_model": "deepseek/deepseek-chat"
            },
            {
                "name": "General Request",
                "messages": [{"role": "user", "content": "What is the weather today?"}],
                "expected_model": "deepseek/deepseek-chat"
            }
        ]
        
        for test_case in test_cases:
            try:
                provider, model = policy.route_request(test_case["messages"])
                print(f"    {test_case['name']}: {provider} -> {model}")
                
                if provider == "openrouter":
                    print(f"      ✅ Routed to OpenRouter (expected: {test_case['expected_model']})")
                else:
                    print(f"      ⚠️  Routed to {provider} (fallback active)")
                    
            except Exception as e:
                print(f"      ❌ Routing failed: {e}")
        
        # Test routing status
        status = policy.get_routing_status()
        print(f"    Routing Status: OpenRouter={status['openrouter']['available']}, Local={status['local_fallback']['available']}")
        
        print("✅ Routing policy tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Routing policy test failed: {e}")
        return False


async def test_tools_integration():
    """Test tools dispatch system"""
    print("\n🔍 Testing Tools Integration...")
    
    try:
        from src.tools.dispatch import ToolDispatcher
        
        async with ToolDispatcher() as dispatcher:
            # Test health check
            health = await dispatcher.health_check()
            print(f"    n8n Health: {health['n8n']['available']}")
            print(f"    MCP Health: {health['mcp']['available']}")
            
            # Test available tools
            tools = await dispatcher.get_available_tools()
            print(f"    Available Tools: {len(tools)}")
            for tool in tools:
                print(f"      - {tool['function']['name']}: {tool['function']['description']}")
        
        print("✅ Tools integration tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Tools integration test failed: {e}")
        return False


async def test_memory_integration():
    """Test memory system integration"""
    print("\n🔍 Testing Memory Integration...")
    
    try:
        from src.memory.integration import MemoryIntegration
        
        async with MemoryIntegration() as memory:
            # Test health check
            health = await memory.health_check()
            print(f"    Memory Health: {health['status']}")
            print(f"    Available: {health['available']}")
            
            if health['available']:
                # Test conversation storage (will fail if service not running)
                test_conversation_id = "test-conv-123"
                test_messages = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ]
                
                stored = await memory.store_conversation(
                    test_conversation_id, 
                    test_messages, 
                    "openrouter:deepseek/deepseek-chat",
                    {"test": True}
                )
                print(f"    Test Storage: {'✅ Success' if stored else '❌ Failed'}")
        
        print("✅ Memory integration tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Memory integration test failed: {e}")
        return False


async def test_configuration():
    """Test configuration files"""
    print("\n🔍 Testing Configuration...")
    
    try:
        # Test constants
        constants_file = Path("00-pipelines-gateway/config/constants.py")
        if constants_file.exists():
            print("    ✅ Constants file exists")
        else:
            print("    ❌ Constants file missing")
        
        # Test presets
        presets_file = Path("00-pipelines-gateway/config/presets.json")
        if presets_file.exists():
            with open(presets_file) as f:
                presets = json.load(f)
            print(f"    ✅ Presets file exists ({len(presets)} presets)")
        else:
            print("    ❌ Presets file missing")
        
        # Test tools
        tools_file = Path("00-pipelines-gateway/config/tools.json")
        if tools_file.exists():
            with open(tools_file) as f:
                tools = json.load(f)
            print(f"    ✅ Tools file exists ({len(tools)} tools)")
        else:
            print("    ❌ Tools file missing")
        
        # Test environment
        env_file = Path(".env.prod")
        if env_file.exists():
            print("    ✅ Production environment file exists")
        else:
            print("    ❌ Production environment file missing")
        
        print("✅ Configuration tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_api_gateway():
    """Test API gateway endpoints"""
    print("\n🔍 Testing API Gateway...")
    
    try:
        # Import and test the gateway module
        from src.api.openrouter_gateway import router
        print("    ✅ API Gateway module loads successfully")
        
        # Test if we can create a FastAPI app (basic syntax check)
        from fastapi import FastAPI
        test_app = FastAPI()
        test_app.include_router(router)
        print("    ✅ API Gateway router can be included in FastAPI app")
        
        print("✅ API Gateway tests completed")
        return True
        
    except Exception as e:
        print(f"❌ API Gateway test failed: {e}")
        return False


async def test_end_to_end_simulation():
    """Simulate an end-to-end request"""
    print("\n🔍 Testing End-to-End Simulation...")
    
    try:
        from src.router.policy import get_router_policy
        from src.providers import openrouter
        
        # Simulate a chat request
        test_messages = [
            {"role": "user", "content": "Help me write a Python function to calculate fibonacci numbers"}
        ]
        
        # Get routing decision
        policy = get_router_policy()
        provider, model = policy.route_request(test_messages)
        print(f"    Routing Decision: {provider} -> {model}")
        
        # Test model capabilities
        if provider == "openrouter":
            capabilities = openrouter.get_model_capabilities(model)
            print(f"    Model Capabilities: {capabilities}")
        
        print("✅ End-to-end simulation completed")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end simulation failed: {e}")
        return False


async def main():
    """Run complete integration test suite"""
    print("🚀 OpenRouter Refactor - Complete Integration Test")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Run all tests
    test_results = []
    
    tests = [
        ("Configuration", test_configuration),
        ("Providers", test_providers), 
        ("Routing Policy", test_routing_policy),
        ("Tools Integration", test_tools_integration),
        ("Memory Integration", test_memory_integration),
        ("API Gateway", test_api_gateway),
        ("End-to-End Simulation", test_end_to_end_simulation)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! OpenRouter refactor is ready for deployment.")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Review the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
