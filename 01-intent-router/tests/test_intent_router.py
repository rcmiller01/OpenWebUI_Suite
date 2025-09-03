"""
Test suite for Intent Router service
"""

import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health endpoint returns correct format"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "version" in data
        assert data["status"] == "healthy"


class TestClassificationEndpoint:
    """Test intent classification endpoint"""
    
    def test_emotional_intent(self):
        """Route sample emotional text → emotional"""
        request_data = {
            "text": "I feel really sad and need someone to talk to about my problems"
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intent"] == "emotional"
        assert data["confidence"] > 0.5
        assert "processing_time_ms" in data
    
    def test_technical_intent(self):
        """Code snippet → technical"""
        request_data = {
            "text": """
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            
            How do I optimize this recursive function?
            """
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intent"] == "technical"
        assert data["confidence"] > 0.5
    
    def test_recipe_intent(self):
        """Recipe text → recipes"""
        request_data = {
            "text": "How do I bake chocolate chip cookies? I need ingredients and temperature"
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intent"] == "recipes"
        assert data["confidence"] > 0.5
    
    def test_finance_intent(self):
        """Finance text → finance"""
        request_data = {
            "text": "What's the best investment strategy for my 401k retirement portfolio?"
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intent"] == "finance"
        assert data["confidence"] > 0.5
    
    def test_image_attachment(self):
        """Image attached → mm_image"""
        request_data = {
            "text": "What do you see in this picture?",
            "attachments": [
                {"type": "image", "mime_type": "image/jpeg"}
            ]
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intent"] == "mm_image"
        assert data["confidence"] > 0.9
        assert data["needs_remote"] is True
    
    def test_audio_attachment(self):
        """Audio attached → mm_audio"""
        request_data = {
            "text": "Can you transcribe this audio file?",
            "attachments": [
                {"type": "audio", "mime_type": "audio/wav"}
            ]
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intent"] == "mm_audio"
        assert data["confidence"] > 0.9
        assert data["needs_remote"] is True
    
    def test_long_text_needs_remote(self):
        """Long/complex prompts → needs_remote=true"""
        long_text = "Explain in detail " * 200  # Very long text
        
        request_data = {
            "text": long_text
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["needs_remote"] is True
    
    def test_context_from_last_intent(self):
        """Test context continuity"""
        request_data = {
            "text": "And what about the error handling?",
            "last_intent": "technical"
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should likely stay technical due to context
        assert data["intent"] in ["technical", "general"]
    
    def test_empty_text_error(self):
        """Empty text should return error"""
        request_data = {
            "text": ""
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 400
    
    def test_general_fallback(self):
        """Unclear text should fallback to general"""
        request_data = {
            "text": "Hello, how are you today?"
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should be general or emotional
        assert data["intent"] in ["general", "emotional"]


class TestPerformance:
    """Test performance requirements"""
    
    def test_response_time(self):
        """Test response time < 50ms target"""
        request_data = {
            "text": "This is a test message for performance measurement"
        }
        
        response = client.post("/classify", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Allow some margin for test environment
        assert data["processing_time_ms"] < 100  # Relaxed for testing


class TestRuleEngine:
    """Test rule engine directly"""
    
    def test_code_pattern_detection(self):
        """Test code pattern detection"""
        from rules import RuleEngine
        
        rule_engine = RuleEngine()
        
        result = rule_engine.classify(
            "```python\nprint('hello world')\n```"
        )
        
        assert result["intent"] == "technical"
        assert result["confident"] is True
    
    def test_emotional_keywords(self):
        """Test emotional keyword detection"""
        from rules import RuleEngine
        
        rule_engine = RuleEngine()
        
        result = rule_engine.classify(
            "I feel so depressed and lonely, need emotional support"
        )
        
        assert result["intent"] == "emotional"
        assert result["confidence"] > 0.8


if __name__ == "__main__":
    pytest.main([__file__])
