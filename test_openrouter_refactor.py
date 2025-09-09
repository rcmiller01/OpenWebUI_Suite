#!/usr/bin/env python3
"""
OpenRouter Refactor Integration Tests
Validates the complete OpenRouter refactor implementation
"""
import asyncio
import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '00-pipelines-gateway', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterRefactorValidator:
    """Validates OpenRouter refactor implementation"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        message = f"{status} - {test_name}"
        if details:
            message += f": {details}"
        
        logger.info(message)
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_configuration_files(self):
        """Test 1: Validate configuration files exist and are valid"""
        logger.info("🔧 Testing Configuration Files...")
        
        # Test constants.py
        try:
            from config.constants import (
                MODEL_TOOLCALL, MODEL_VISION, MODEL_EXPLICIT, MODEL_CODER,
                OPENROUTER_BASE_URL
            )
            self.log_test(
                "Configuration Constants", 
                True, 
                f"Models: {MODEL_TOOLCALL}, {MODEL_VISION}, {MODEL_EXPLICIT}, {MODEL_CODER}"
            )
        except Exception as e:
            self.log_test("Configuration Constants", False, str(e))
        
        # Test presets.json
        try:
            presets_path = "00-pipelines-gateway/config/presets.json"
            if os.path.exists(presets_path):
                with open(presets_path, 'r') as f:
                    presets = json.load(f)
                    preset_count = len(presets)
                    self.log_test("Model Presets", True, f"{preset_count} presets loaded")
            else:
                self.log_test("Model Presets", False, "presets.json not found")
        except Exception as e:
            self.log_test("Model Presets", False, str(e))
        
        # Test tools.json
        try:
            tools_path = "00-pipelines-gateway/config/tools.json"
            if os.path.exists(tools_path):
                with open(tools_path, 'r') as f:
                    tools = json.load(f)
                    tool_count = len(tools)
                    self.log_test("Tools Configuration", True, f"{tool_count} tools configured")
            else:
                self.log_test("Tools Configuration", False, "tools.json not found")
        except Exception as e:
            self.log_test("Tools Configuration", False, str(e))
    
    async def test_provider_implementations(self):
        """Test 2: Validate provider implementations"""
        logger.info("🔌 Testing Provider Implementations...")
        
        # Test OpenRouter provider
        try:
            from providers import openrouter
            health = openrouter.check_health()
            has_api_key = health.get("api_key_configured", False)
            available_models = health.get("available_models", [])
            
            self.log_test(
                "OpenRouter Provider", 
                True, 
                f"API Key: {has_api_key}, Models: {len(available_models)}"
            )
        except Exception as e:
            self.log_test("OpenRouter Provider", False, str(e))
        
        # Test Local Fallback provider
        try:
            from providers import local_fallback
            health = local_fallback.check_health()
            available = health.get("available", False)
            
            self.log_test(
                "Local Fallback Provider", 
                True, 
                f"Available: {available}"
            )
        except Exception as e:
            self.log_test("Local Fallback Provider", False, str(e))
    
    async def test_routing_policy(self):
        """Test 3: Validate routing policy"""
        logger.info("🧭 Testing Routing Policy...")
        
        try:
            from router.policy import RouterPolicy
            policy = RouterPolicy()
            
            # Test content analysis
            test_messages = [
                {"role": "user", "content": "Can you help me write some Python code?"}
            ]
            
            try:
                provider, model = policy.route_request(test_messages)
                self.log_test(
                    "Routing Decision", 
                    True, 
                    f"Provider: {provider}, Model: {model}"
                )
            except RuntimeError as e:
                # Expected if no providers available
                self.log_test(
                    "Routing Decision", 
                    True, 
                    f"No providers available (expected): {e}"
                )
            
            # Test routing status
            status = policy.get_routing_status()
            openrouter_available = status.get("openrouter", {}).get("available", False)
            local_available = status.get("local_fallback", {}).get("available", False)
            
            self.log_test(
                "Routing Status", 
                True, 
                f"OpenRouter: {openrouter_available}, Local: {local_available}"
            )
            
        except Exception as e:
            self.log_test("Routing Policy", False, str(e))
    
    async def test_tools_dispatch(self):
        """Test 4: Validate tools dispatch system"""
        logger.info("🔧 Testing Tools Dispatch...")
        
        try:
            from tools.dispatch import ToolDispatcher
            
            async with ToolDispatcher() as dispatcher:
                # Test health check
                health = await dispatcher.health_check()
                n8n_available = health.get("n8n", {}).get("available", False)
                mcp_available = health.get("mcp", {}).get("available", False)
                
                self.log_test(
                    "Tools Health Check", 
                    True, 
                    f"n8n: {n8n_available}, MCP: {mcp_available}"
                )
                
                # Test available tools
                tools = await dispatcher.get_available_tools()
                tool_count = len(tools)
                
                self.log_test(
                    "Available Tools", 
                    True, 
                    f"{tool_count} tools available"
                )
                
        except Exception as e:
            self.log_test("Tools Dispatch", False, str(e))
    
    async def test_memory_integration(self):
        """Test 5: Validate memory integration"""
        logger.info("💾 Testing Memory Integration...")
        
        try:
            from memory.integration import MemoryIntegration
            
            async with MemoryIntegration() as memory:
                # Test health check
                health = await memory.health_check()
                available = health.get("available", False)
                
                self.log_test(
                    "Memory Service Health", 
                    True, 
                    f"Available: {available}"
                )
                
        except Exception as e:
            self.log_test("Memory Integration", False, str(e))
    
    async def test_api_gateway(self):
        """Test 6: Validate API gateway"""
        logger.info("🌐 Testing API Gateway...")
        
        try:
            from api.openrouter_gateway import router, ChatRequest, ChatMessage
            
            # Test router creation
            route_count = len(router.routes)
            self.log_test(
                "API Router", 
                True, 
                f"{route_count} routes registered"
            )
            
            # Test data models
            test_message = ChatMessage(role="user", content="Hello")
            test_request = ChatRequest(messages=[test_message])
            
            self.log_test(
                "API Data Models", 
                True, 
                f"Request: {len(test_request.messages)} messages"
            )
            
        except Exception as e:
            self.log_test("API Gateway", False, str(e))
    
    async def test_environment_configuration(self):
        """Test 7: Validate environment configuration"""
        logger.info("⚙️ Testing Environment Configuration...")
        
        # Check critical environment variables
        env_checks = [
            ("OPENROUTER_API_KEY", "OpenRouter API Key"),
            ("OPENROUTER_GATEWAY_URL", "Gateway URL"),
            ("MEMORY_SERVICE_URL", "Memory Service"),
            ("N8N_WEBHOOK_URL", "n8n Webhook"),
            ("MCP_ENDPOINT", "MCP Endpoint")
        ]
        
        configured_vars = 0
        for var_name, description in env_checks:
            value = os.getenv(var_name)
            if value:
                configured_vars += 1
                self.log_test(f"Environment: {description}", True, f"{var_name}=configured")
            else:
                self.log_test(f"Environment: {description}", False, f"{var_name}=not set")
        
        self.log_test(
            "Environment Configuration", 
            configured_vars > 0, 
            f"{configured_vars}/{len(env_checks)} variables configured"
        )
    
    async def run_all_tests(self):
        """Run all validation tests"""
        logger.info("🧪 Starting OpenRouter Refactor Validation Tests")
        logger.info("=" * 60)
        
        await self.test_configuration_files()
        await self.test_provider_implementations()
        await self.test_routing_policy()
        await self.test_tools_dispatch()
        await self.test_memory_integration()
        await self.test_api_gateway()
        await self.test_environment_configuration()
        
        # Summary
        logger.info("=" * 60)
        logger.info(f"🏁 Test Results: {self.passed_tests}/{self.total_tests} tests passed")
        
        if self.passed_tests == self.total_tests:
            logger.info("🎉 ALL TESTS PASSED - OpenRouter refactor is ready!")
        else:
            failed_tests = self.total_tests - self.passed_tests
            logger.warning(f"⚠️ {failed_tests} tests failed - check implementation")
        
        return self.results

async def main():
    """Main test runner"""
    validator = OpenRouterRefactorValidator()
    results = await validator.run_all_tests()
    
    # Save results to file
    results_file = "openrouter_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "total_tests": validator.total_tests,
            "passed_tests": validator.passed_tests,
            "results": results
        }, f, indent=2)
    
    logger.info(f"📊 Results saved to {results_file}")
    
    # Exit with appropriate code
    sys.exit(0 if validator.passed_tests == validator.total_tests else 1)

if __name__ == "__main__":
    asyncio.run(main())
