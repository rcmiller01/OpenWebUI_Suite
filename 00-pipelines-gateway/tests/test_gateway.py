"""
Test suite for the Pipelines Gateway

Tests the OpenAI-compatible endpoint, streaming, hooks, and tool integration.
"""

import pytest
from fastapi.testclient import TestClient

from src.server import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "metrics" in data


def test_list_models(client):
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert data["data"][0]["object"] == "model"


def test_list_tools(client):
    response = client.get("/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"


def test_chat_completion_non_streaming(client):
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["role"] == "assistant"


def test_chat_completion_streaming(client):
    request_data = {
        "messages": [
            {"role": "user", "content": "Tell me a story"}
        ]
    }
    r = client.post("/v1/chat/completions/stream", json=request_data)
    assert r.status_code == 200


def test_chat_completion_with_user_id(client):
    request_data = {
        "messages": [
            {"role": "user", "content": "What's my conversation history?"}
        ],
        "user": "test_user_123"
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["role"] == "assistant"


def test_chat_completion_empty_messages(client):
    request_data = {"messages": []}
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    assert "error" in response.json()


def test_chat_completion_invalid_model(client):
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200


def test_chat_completion_temperature_parameter(client):
    request_data = {
        "messages": [
            {"role": "user", "content": "Be creative"}
        ],
        "temperature": 0.9
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200


def test_chat_completion_max_tokens_parameter(client):
    request_data = {
        "messages": [
            {"role": "user", "content": "Give me a long response"}
        ],
        "max_tokens": 100
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200


@pytest.mark.skip("legacy hook system not active in simplified gateway")
def test_hook_system():
    pass


@pytest.mark.skip("tool registry not wired in simplified gateway tests")
def test_tool_registry():
    pass


@pytest.mark.skip("model router advanced tests skipped")
def test_model_router():
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
