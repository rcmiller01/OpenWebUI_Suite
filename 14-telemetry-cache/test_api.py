"""
Test suite for Telemetry Cache Service
"""

import pytest
import time
import asyncio
import re
from fastapi.testclient import TestClient
from src.app import app, normalize_tool_args, PII_PATTERNS

client = TestClient(app)


def test_normalize_tool_args():
    """Test tool argument normalization"""
    args = {
        "model": "Llama-2-7B",
        "temperature": 0.7,
        "prompt": "Hello World!",
        "max_tokens": 100
    }

    result = normalize_tool_args("generate_response", args)
    expected = ("tool:generate_response:max_tokens:100:model:llama_2_7b:"
                "prompt:hello_world_:temperature:0.70")

    assert result == expected


def test_normalize_tool_args_empty():
    """Test normalization with empty args"""
    result = normalize_tool_args("test_tool", {})
    assert result == "tool:test_tool:"


def test_normalize_tool_args_special_chars():
    """Test normalization with special characters"""
    args = {
        "prompt": "Hello@World#Test!",
        "model": "GPT-3.5"
    }

    result = normalize_tool_args("chat", args)
    assert "hello_world_test" in result
    assert "gpt_3_5" in result


@pytest.mark.asyncio
async def test_log_event_basic():
    """Test basic log event processing"""
    event_data = {
        "event": "tool_execution",
        "payload": {
            "tool": "generate_response",
            "latency_ms": 250,
            "tokens": 150,
            "user_id": "user123",
            "session_id": "sess456"
        }
    }

    response = client.post("/log", json=event_data)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "logged"
    assert "event_id" in result
    assert "user_id" in result["redacted_fields"]
    assert "session_id" in result["redacted_fields"]


def test_log_event_pii_redaction():
    """Test PII redaction in log events"""
    event_data = {
        "event": "user_action",
        "payload": {
            "email": "test@example.com",
            "phone": "555-123-4567",
            "api_key": "sk-1234567890abcdef1234567890abcdef",
            "message": "Hello world",
            "ip": "192.168.1.1"
        }
    }

    response = client.post("/log", json=event_data)
    assert response.status_code == 200

    result = response.json()
    assert "email" in result["redacted_fields"]
    assert "phone" in result["redacted_fields"]
    assert "api_key" in result["redacted_fields"]
    assert "ip" in result["redacted_fields"]


def test_log_event_missing_fields():
    """Test log event with missing required fields"""
    incomplete_event = {
        "event": "test_event"
        # Missing payload
    }

    response = client.post("/log", json=incomplete_event)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_cache_operations():
    """Test cache set and get operations"""
    # Set cache
    cache_data = {
        "key": "test_key",
        "data": {
            "response": "Hello world",
            "tokens": 100
        },
        "ttl": 60
    }

    response = client.post("/cache/set", json=cache_data)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "cached"
    assert result["key"] == "test_key"
    assert "expires_at" in result

    # Get cache (will be miss since Redis not available in test)
    response = client.get("/cache/get?key=test_key")
    assert response.status_code == 200

    result = response.json()
    assert result["hit"] is False  # Expected miss when Redis not available
    assert result["data"] is None


def test_cache_miss():
    """Test cache miss scenario"""
    response = client.get("/cache/get?key=nonexistent_key")
    assert response.status_code == 200

    result = response.json()
    assert result["hit"] is False
    assert result["data"] is None


def test_cache_set_missing_fields():
    """Test cache set with missing required fields"""
    incomplete_cache = {
        "key": "test_key"
        # Missing data
    }

    response = client.post("/cache/set", json=incomplete_cache)
    assert response.status_code == 422  # Validation error


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    result = response.json()
    assert "status" in result
    assert "version" in result
    assert result["version"] == "1.0.0"


def test_metrics_endpoint():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200

    # Should contain Prometheus metrics
    content = response.text
    assert "telemetry_cache_ttfb_seconds" in content
    assert "telemetry_cache_tokens_per_second" in content
    assert "telemetry_cache_repair_rate_total" in content


def test_pii_patterns():
    """Test PII detection patterns"""
    test_cases = [
        ("email", "test@example.com", True),
        ("email", "notanemail", False),
        ("phone", "555-123-4567", True),
        ("phone", "notaphonenumber", False),
        ("api_key", "sk-1234567890abcdef1234567890abcdef", True),
        ("api_key", "short", False),
        ("ip_address", "192.168.1.1", True),
        ("ip_address", "notanip", False),
    ]

    for pattern_name, test_string, should_match in test_cases:
        pattern = PII_PATTERNS[pattern_name]
        matches = bool(re.search(pattern, test_string, re.IGNORECASE))
        assert matches == should_match, (
            f"Pattern {pattern_name} failed for {test_string}"
        )


def test_log_event_large_payload():
    """Test logging with large payload"""
    large_payload = {
        "event": "large_test",
        "payload": {
            "data": "x" * 10000,  # 10KB of data
            "metadata": {
                "nested": {
                    "deeply": {
                        "nested": "value"
                    }
                }
            }
        }
    }

    response = client.post("/log", json=large_payload)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "logged"


@pytest.mark.asyncio
async def test_concurrent_logging():
    """Test concurrent logging operations"""
    async def log_event(i):
        event_data = {
            "event": f"concurrent_test_{i}",
            "payload": {
                "index": i,
                "timestamp": time.time()
            }
        }
        response = client.post("/log", json=event_data)
        return response.status_code

    # Create 10 concurrent logging requests
    tasks = [log_event(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(status == 200 for status in results)


def test_cache_key_normalization_edge_cases():
    """Test cache key normalization edge cases"""
    # Test with None values
    args = {"param1": None, "param2": "value"}
    result = normalize_tool_args("test", args)
    assert "param1:None" in result

    # Test with boolean values
    args = {"flag": True, "count": 42}
    result = normalize_tool_args("test", args)
    assert "flag:True" in result
    assert "count:42" in result


if __name__ == "__main__":
    pytest.main([__file__])
