"""
Test suite for the Pipelines Gateway

Tests the OpenAI-compatible endpoint, streaming, hooks, and tool integration.
"""

import asyncio
import json
from typing import AsyncGenerator

import httpx
import pytest
from fastapi.testclient import TestClient

from src.server import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "components" in data


def test_list_models(client):
    """Test the models listing endpoint"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert len(data["data"]) > 0
    
    # Check model format
    model = data["data"][0]
    assert "id" in model
    assert "object" in model
    assert model["object"] == "model"


def test_list_tools(client):
    """Test the tools listing endpoint"""
    response = client.get("/v1/tools")
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert len(data["data"]) > 0
    
    # Check tool format
    tool = data["data"][0]
    assert tool["type"] == "function"
    assert "function" in tool
    assert "name" in tool["function"]
    assert "description" in tool["function"]


def test_chat_completion_non_streaming(client):
    """Test non-streaming chat completion"""
    request_data = {
        "model": "mock-model",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert len(data["choices"]) > 0
    
    choice = data["choices"][0]
    assert "message" in choice
    assert choice["message"]["role"] == "assistant"
    assert len(choice["message"]["content"]) > 0


def test_chat_completion_streaming(client):
    """Test streaming chat completion"""
    request_data = {
        "model": "mock-model",
        "messages": [
            {"role": "user", "content": "Tell me a story"}
        ],
        "stream": True
    }
    
    with client.stream("POST", "/v1/chat/completions", json=request_data) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        
        chunks_received = 0
        for chunk in response.iter_lines():
            if chunk.startswith("data: "):
                chunks_received += 1
                chunk_data = chunk[6:]  # Remove "data: " prefix
                
                if chunk_data == "[DONE]":
                    break
                
                try:
                    parsed = json.loads(chunk_data)
                    assert "id" in parsed
                    assert parsed["object"] == "chat.completion.chunk"
                    assert "choices" in parsed
                except json.JSONDecodeError:
                    # Skip malformed chunks
                    pass
        
        assert chunks_received > 0


def test_chat_completion_with_user_id(client):
    """Test chat completion with user identification"""
    request_data = {
        "model": "mock-model",
        "messages": [
            {"role": "user", "content": "What's my conversation history?"}
        ],
        "user": "test_user_123",
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0


def test_chat_completion_empty_messages(client):
    """Test chat completion with empty messages"""
    request_data = {
        "model": "mock-model",
        "messages": [],
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 500  # Should fail validation


def test_chat_completion_invalid_model(client):
    """Test chat completion with non-existent model"""
    request_data = {
        "model": "non-existent-model",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=request_data)
    # Should still work due to fallback routing
    assert response.status_code == 200


def test_chat_completion_temperature_parameter(client):
    """Test chat completion with temperature parameter"""
    request_data = {
        "model": "mock-model",
        "messages": [
            {"role": "user", "content": "Be creative"}
        ],
        "temperature": 0.9,
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200


def test_chat_completion_max_tokens_parameter(client):
    """Test chat completion with max_tokens parameter"""
    request_data = {
        "model": "mock-model",
        "messages": [
            {"role": "user", "content": "Give me a long response"}
        ],
        "max_tokens": 100,
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_hook_system():
    """Test that hooks are being called"""
    from src.hooks.pre import run_pre_hooks
    from src.hooks.mid import run_mid_hooks
    from src.hooks.post import run_post_hooks
    from src.server import PipelineContext, ChatMessage
    
    # Create test context
    ctx = PipelineContext(
        user_id="test_user",
        request_id="test_123",
        messages=[ChatMessage(role="user", content="Test message")],
        model="mock-model"
    )
    
    # Test pre-hooks
    ctx = await run_pre_hooks(ctx)
    assert ctx.intent is not None
    assert ctx.memory is not None
    assert ctx.metadata["authenticated"] is not None
    
    # Test mid-hooks
    ctx = await run_mid_hooks(ctx)
    assert "available_tools" in ctx.metadata
    assert "tuned_temperature" in ctx.metadata
    
    # Test post-hooks
    ctx = await run_post_hooks(ctx)
    assert "analytics" in ctx.metadata


@pytest.mark.asyncio
async def test_tool_registry():
    """Test tool registry functionality"""
    from src.tools.registry import ToolRegistry
    
    registry = ToolRegistry()
    await registry.load_config()
    
    # Test listing tools
    tools = await registry.list_tools()
    assert len(tools) > 0
    
    # Test calculator tool
    calc_result = await registry.execute_tool("calculator", expression="2 + 2")
    assert calc_result["success"] is True
    assert calc_result["result"] == 4
    
    # Test web search tool
    search_result = await registry.execute_tool("web_search", query="python")
    assert search_result["success"] is True
    assert "results" in search_result


@pytest.mark.asyncio
async def test_model_router():
    """Test model routing functionality"""
    from src.router.model_map import ModelRouter
    from src.server import PipelineContext, ChatMessage
    
    router = ModelRouter()
    await router.load_config()
    
    # Test model listing
    models = await router.list_models()
    assert len(models) > 0
    
    # Test model routing
    ctx = PipelineContext(
        user_id="test",
        request_id="test",
        messages=[ChatMessage(role="user", content="Analyze this data")],
        model="gpt-4"
    )
    ctx.intent = "analysis"
    
    routed_model = await router.route_model("non-existent-model", ctx)
    assert routed_model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
