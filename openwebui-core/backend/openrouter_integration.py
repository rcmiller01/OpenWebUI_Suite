# OpenWebUI Core Integration for OpenRouter Gateway
# Add this to your OpenWebUI backend configuration

import os
import httpx
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# OpenRouter Gateway Configuration
OPENROUTER_GATEWAY_URL = os.getenv(
    "OPENROUTER_GATEWAY_URL", 
    "http://00-pipelines-gateway:8000"
)
OPENROUTER_GATEWAY_TIMEOUT = int(os.getenv("OPENROUTER_GATEWAY_TIMEOUT", "60"))


class OpenRouterGatewayClient:
    """Client for OpenRouter Gateway integration"""
    
    def __init__(self):
        self.base_url = OPENROUTER_GATEWAY_URL
        self.timeout = OPENROUTER_GATEWAY_TIMEOUT
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]],
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: int = 1200,
                             tools: Optional[List[Dict[str, Any]]] = None,
                             conversation_id: Optional[str] = None,
                             stream: bool = False) -> Dict[str, Any]:
        """
        Send chat completion request to OpenRouter Gateway
        """
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if model:
            payload["model"] = model
        if tools:
            payload["tools"] = tools
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"OpenRouter Gateway request failed: {e}")
                raise
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get available models from OpenRouter Gateway"""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/models")
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"Failed to get models from gateway: {e}")
                return {"openrouter": [], "local_fallback": []}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check gateway health"""
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/health")
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"Gateway health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}
    
    async def get_routing_status(self) -> Dict[str, Any]:
        """Get current routing status"""
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/routing/status")
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"Failed to get routing status: {e}")
                return {"routing_enabled": False, "error": str(e)}


# Global gateway client instance
_gateway_client = None


def get_gateway_client() -> OpenRouterGatewayClient:
    """Get or create the global gateway client"""
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = OpenRouterGatewayClient()
    return _gateway_client


# Integration helper functions for OpenWebUI
async def openrouter_chat_completion(messages: List[Dict[str, str]], 
                                    **kwargs) -> Dict[str, Any]:
    """OpenWebUI compatible chat completion function"""
    client = get_gateway_client()
    return await client.chat_completion(messages, **kwargs)


async def get_openrouter_models() -> List[Dict[str, str]]:
    """Get OpenRouter models in OpenWebUI format"""
    client = get_gateway_client()
    models_data = await client.get_available_models()
    
    # Convert to OpenWebUI format
    models = []
    
    # Add OpenRouter models
    for model in models_data.get("openrouter", []):
        models.append({
            "id": model,
            "name": f"OpenRouter: {model}",
            "object": "model",
            "provider": "openrouter"
        })
    
    # Add local fallback
    for model in models_data.get("local_fallback", []):
        models.append({
            "id": f"local/{model}",
            "name": f"Local: {model}",
            "object": "model", 
            "provider": "local_fallback"
        })
    
    return models


async def check_openrouter_gateway_health() -> bool:
    """Check if OpenRouter Gateway is healthy"""
    client = get_gateway_client()
    health = await client.health_check()
    return health.get("status") == "healthy"
