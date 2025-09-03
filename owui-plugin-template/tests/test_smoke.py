"""Smoke tests for the OpenWebUI Plugin Template."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from owui_plugin_template.plugin import register


@pytest.fixture
def app():
    """Create a FastAPI app with the plugin registered."""
    test_app = FastAPI()
    register(test_app)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_plugin_registration(app):
    """Test that the plugin registers without errors."""
    # If we get here without exceptions, the plugin registered successfully
    assert app is not None
    
    # Check that routes were added
    routes = [route.path for route in app.routes]
    assert "/ext/template/health" in routes
    assert "/ext/template/info" in routes


def test_health_endpoint(client):
    """Test the health endpoint returns expected response."""
    response = client.get("/ext/template/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert data["plugin"] == "template"
    assert data["version"] == "0.1.0"


def test_info_endpoint(client):
    """Test the info endpoint returns plugin metadata."""
    response = client.get("/ext/template/info")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "OpenWebUI Plugin Template"
    assert data["version"] == "0.1.0"
    assert "capabilities" in data
    assert "endpoints" in data
    assert isinstance(data["capabilities"], list)
    assert isinstance(data["endpoints"], list)


def test_health_endpoint_schema(client):
    """Test that the health endpoint follows the expected schema."""
    response = client.get("/ext/template/health")
    data = response.json()
    
    # Verify required fields are present
    required_fields = ["ok", "plugin", "version"]
    for field in required_fields:
        assert field in data
    
    # Verify field types
    assert isinstance(data["ok"], bool)
    assert isinstance(data["plugin"], str)
    assert isinstance(data["version"], str)
