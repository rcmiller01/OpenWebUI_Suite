"""Ollama API client and utilities."""

import time
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel


class OllamaModel(BaseModel):
    """Ollama model information."""
    name: str
    size: int
    digest: str
    modified_at: str


class OllamaModelsResponse(BaseModel):
    """Response from Ollama /api/tags endpoint."""
    models: List[OllamaModel]


class OllamaHealthStatus(BaseModel):
    """Health status response for Ollama service."""
    ok: bool
    ollama_host: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    models_count: Optional[int] = None


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, host: str, timeout: float = 5.0) -> None:
        """Initialize the Ollama client.
        
        Args:
            host: The Ollama host URL (e.g., "http://localhost:11434")
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip("/")
        self.timeout = timeout
    
    async def health_check(self) -> OllamaHealthStatus:
        """Check the health of the Ollama service.
        
        Returns:
            OllamaHealthStatus with health information and latency.
        """
        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                
                # Calculate latency
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                
                # Count models
                data = response.json()
                models_count = len(data.get("models", []))
                
                return OllamaHealthStatus(
                    ok=True,
                    ollama_host=self.host,
                    latency_ms=latency_ms,
                    models_count=models_count
                )
                
        except Exception as e:
            return OllamaHealthStatus(
                ok=False,
                ollama_host=self.host,
                error=str(e)
            )
    
    async def get_models(self) -> List[OllamaModel]:
        """Get the list of available models from Ollama.
        
        Returns:
            List of OllamaModel instances.
            
        Raises:
            httpx.HTTPError: If the request fails.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models_response = OllamaModelsResponse(**data)
            return models_response.models
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model to get info for.
            
        Returns:
            Model information dictionary or None if not found.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.host}/api/show",
                    json={"name": model_name}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            return None
    
    async def route_model(
        self, 
        prompt: str, 
        criteria: Dict[str, Any]
    ) -> Optional[str]:
        """Simple model routing based on criteria.
        
        This is a basic implementation that could be extended with
        more sophisticated routing logic.
        
        Args:
            prompt: The input prompt
            criteria: Routing criteria (size, tags, etc.)
            
        Returns:
            Recommended model name or None if no suitable model found.
        """
        try:
            models = await self.get_models()
            
            # Simple routing logic - prefer smaller models for short prompts
            if len(prompt) < 100:
                # Prefer smaller models for short prompts
                models.sort(key=lambda x: x.size)
            else:
                # Prefer larger models for longer prompts
                models.sort(key=lambda x: x.size, reverse=True)
            
            # Return the first model that meets criteria
            for model in models:
                if self._matches_criteria(model, criteria):
                    return model.name
            
            # Fallback to first available model
            return models[0].name if models else None
            
        except Exception:
            return None
    
    def _matches_criteria(self, model: OllamaModel, criteria: Dict[str, Any]) -> bool:
        """Check if a model matches the given criteria.
        
        Args:
            model: The model to check
            criteria: Criteria to match against
            
        Returns:
            True if the model matches all criteria, False otherwise.
        """
        # Size constraints
        if "max_size" in criteria and model.size > criteria["max_size"]:
            return False
        
        if "min_size" in criteria and model.size < criteria["min_size"]:
            return False
        
        # Name pattern matching
        if "name_pattern" in criteria:
            pattern = criteria["name_pattern"].lower()
            if pattern not in model.name.lower():
                return False
        
        return True
