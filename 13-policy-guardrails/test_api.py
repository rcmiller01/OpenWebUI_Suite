"""
Test suite for Policy Guardrails Service
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "lanes_loaded" in data
    assert "filters_loaded" in data


def test_get_lanes():
    """Test lanes endpoint"""
    response = client.get("/lanes")
    assert response.status_code == 200
    data = response.json()
    assert "lanes" in data
    assert "details" in data
    assert "technical" in data["lanes"]
    assert "emotional" in data["lanes"]
    assert "creative" in data["lanes"]
    assert "analytical" in data["lanes"]


def test_apply_policy_technical():
    """Test technical lane policy application"""
    request_data = {
        "lane": "technical",
        "system": "You are a helpful assistant",
        "user": "How do I write a Python function?",
        "affect": {
            "emotion": "curious",
            "intensity": 0.7
        },
        "drive": {
            "energy": 0.8,
            "focus": 0.9
        }
    }

    response = client.post("/policy/apply", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert "system_final" in data
    assert "validators" in data
    assert "JSON schema" in data["system_final"]
    assert len(data["validators"]) > 0


def test_apply_policy_emotional():
    """Test emotional lane policy application"""
    request_data = {
        "lane": "emotional",
        "system": "You are a helpful assistant",
        "user": "I'm feeling sad today",
        "affect": {
            "emotion": "sad",
            "intensity": 0.8
        },
        "drive": {
            "energy": 0.4,
            "focus": 0.6
        }
    }

    response = client.post("/policy/apply", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert "system_final" in data
    assert "validators" in data
    assert "empathetic assistant" in data["system_final"].lower()


def test_apply_policy_invalid_lane():
    """Test invalid lane handling"""
    request_data = {
        "lane": "invalid_lane",
        "system": "You are a helpful assistant",
        "user": "Test message",
        "affect": {
            "emotion": "neutral",
            "intensity": 0.5
        },
        "drive": {
            "energy": 0.5,
            "focus": 0.5
        }
    }

    response = client.post("/policy/apply", json=request_data)
    assert response.status_code == 400


def test_validate_content_technical_valid():
    """Test technical content validation - valid case"""
    request_data = {
        "lane": "technical",
        "text": '{"explanation": "A function is defined using the def keyword", "code": "def hello(): pass"}'
    }

    response = client.post("/policy/validate", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] == True
    assert len(data["repairs"]) == 0


def test_validate_content_technical_invalid():
    """Test technical content validation - invalid case"""
    request_data = {
        "lane": "technical",
        "text": "Here's some code: eval(user_input)"
    }

    response = client.post("/policy/validate", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] == False
    assert len(data["repairs"]) > 0
    assert any("security" in repair["issue"].lower() for repair in data["repairs"])


def test_validate_content_emotional_valid():
    """Test emotional content validation - valid case"""
    request_data = {
        "lane": "emotional",
        "text": "I understand you're feeling sad. It's okay to feel this way. Would you like to talk about what's bothering you?"
    }

    response = client.post("/policy/validate", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] == True


def test_validate_content_emotional_invalid():
    """Test emotional content validation - invalid case"""
    request_data = {
        "lane": "emotional",
        "text": "You should just get over it and stop being so stupid about everything. This is ridiculous behavior."
    }

    response = client.post("/policy/validate", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] == False
    assert len(data["repairs"]) > 0


def test_validate_content_invalid_lane():
    """Test validation with invalid lane"""
    request_data = {
        "lane": "invalid_lane",
        "text": "Test content"
    }

    response = client.post("/policy/validate", json=request_data)
    assert response.status_code == 400


def test_policy_apply_missing_fields():
    """Test policy apply with missing required fields"""
    incomplete_request = {
        "lane": "technical",
        "system": "Test system"
        # Missing user, affect, drive
    }

    response = client.post("/policy/apply", json=incomplete_request)
    assert response.status_code == 422  # Validation error


def test_policy_validate_missing_fields():
    """Test policy validate with missing required fields"""
    incomplete_request = {
        "lane": "technical"
        # Missing text
    }

    response = client.post("/policy/validate", json=incomplete_request)
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__])
