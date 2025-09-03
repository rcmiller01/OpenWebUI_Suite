"""
Model routing and mapping functionality

Handles model selection, load balancing, and routing to different
providers (local models, OpenRouter, etc.)
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ModelRouter:
    """Router for managing and routing to different models"""
    
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.config_path = "config/models.json"
    
    async def load_config(self):
        """Load model configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.models = config.get("models", {})
            else:
                # Default configuration
                self.models = {
                    "gpt-3.5-turbo": {
                        "provider": "openrouter",
                        "model_id": "openai/gpt-3.5-turbo",
                        "max_tokens": 4096,
                        "cost_per_token": 0.0000015,
                        "capabilities": ["chat", "streaming"]
                    },
                    "gpt-4": {
                        "provider": "openrouter",
                        "model_id": "openai/gpt-4",
                        "max_tokens": 8192,
                        "cost_per_token": 0.00003,
                        "capabilities": ["chat", "streaming", "advanced"]
                    },
                    "claude-3-sonnet": {
                        "provider": "openrouter",
                        "model_id": "anthropic/claude-3-sonnet",
                        "max_tokens": 4096,
                        "cost_per_token": 0.000015,
                        "capabilities": ["chat", "streaming", "analysis"]
                    },
                    "mock-model": {
                        "provider": "local",
                        "model_id": "mock-model",
                        "max_tokens": 2048,
                        "cost_per_token": 0.0,
                        "capabilities": ["chat", "streaming", "development"]
                    }
                }
                
                # Save default config
                await self._save_config()
            
            logger.info(f"Loaded {len(self.models)} model configurations")
            
        except Exception as e:
            logger.error(f"Failed to load model config: {e}")
            raise
    
    async def _save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            config = {"models": self.models}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model config: {e}")
    
    async def route_model(self, requested_model: str, ctx) -> str:
        """
        Route to the best available model
        
        Args:
            requested_model: The model requested by the client
            ctx: PipelineContext with additional routing information
            
        Returns:
            The actual model to use
        """
        logger.debug(f"Routing model '{requested_model}'")
        
        # Check if requested model exists
        if requested_model in self.models:
            return requested_model
        
        # Fallback routing based on intent
        if ctx.intent == "analysis":
            return self._find_best_model(["analysis", "advanced"])
        elif ctx.intent == "generation":
            return self._find_best_model(["chat", "streaming"])
        else:
            return self._find_best_model(["chat"])
    
    def _find_best_model(self, required_capabilities: List[str]) -> str:
        """Find the best model with required capabilities"""
        best_model = None
        best_score = -1
        
        for model_name, config in self.models.items():
            capabilities = config.get("capabilities", [])
            
            # Check if model has required capabilities
            if all(cap in capabilities for cap in required_capabilities):
                # Score based on cost and capabilities
                score = len(capabilities) - config.get("cost_per_token", 1.0) * 1000
                
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model or "mock-model"  # Fallback to mock
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models in OpenAI format"""
        models = []
        
        for model_name, config in self.models.items():
            models.append({
                "id": model_name,
                "object": "model",
                "created": 1677610602,  # Mock timestamp
                "owned_by": config.get("provider", "unknown"),
                "capabilities": config.get("capabilities", []),
                "max_tokens": config.get("max_tokens", 2048)
            })
        
        return models
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        return self.models.get(model_name)
    
    async def call_model(self, model_name: str, messages: List[Dict], **kwargs):
        """
        Call the specified model (placeholder for actual implementation)
        
        In production, this would route to the appropriate provider
        """
        model_config = self.models.get(model_name)
        if not model_config:
            raise ValueError(f"Model '{model_name}' not found")
        
        provider = model_config.get("provider")
        
        if provider == "openrouter":
            return await self._call_openrouter(model_config, messages, **kwargs)
        elif provider == "local":
            return await self._call_local_model(model_config, messages, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_openrouter(self, config: Dict, messages: List[Dict], **kwargs):
        """Call OpenRouter API"""
        if not self.openrouter_key:
            raise ValueError("OpenRouter API key not configured")
        
        # This would make actual API calls to OpenRouter
        # For now, return a mock response
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Mock response from {config['model_id']} via OpenRouter"
                }
            }]
        }
    
    async def _call_local_model(self, config: Dict, messages: List[Dict], **kwargs):
        """Call local model"""
        # This would call local models (Ollama, etc.)
        # For now, return a mock response
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Mock response from local model {config['model_id']}"
                }
            }]
        }
