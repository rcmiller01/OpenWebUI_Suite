"""Main plugin registration module for Ollama Tools."""

import os
from typing import Any, Dict

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from .memory import Memory
from .ollama import OllamaClient


class MemorySetRequest(BaseModel):
    """Request model for setting memory values."""
    key: str
    value: str


class MemoryGetResponse(BaseModel):
    """Response model for getting memory values."""
    ok: bool
    value: str | None


class RouteRequest(BaseModel):
    """Request model for model routing."""
    prompt: str
    criteria: Dict[str, Any] = {}


class RouteResponse(BaseModel):
    """Response model for model routing."""
    ok: bool
    recommended_model: str | None
    reasoning: str


def register(app: FastAPI) -> None:
    """Register the Ollama Tools plugin with the FastAPI application.
    
    Args:
        app: The FastAPI application instance to register routes with.
    """
    # Get configuration from environment
    ollama_host = os.getenv("OLLAMA_HOST", "http://core2-gpu:11434")
    memory_path = os.getenv("OWUI_MEMORY_PATH", "./data/memory.sqlite")
    
    # Initialize services
    ollama_client = OllamaClient(ollama_host)
    memory = Memory(memory_path)
    
    # Create router
    router = APIRouter(prefix="/ext/ollama", tags=["ollama-tools"])
    
    @router.get("/health")
    async def health():
        """Check the health of Ollama service and plugin."""
        ollama_status = await ollama_client.health_check()
        memory_stats = memory.stats()
        
        return {
            "ok": ollama_status.ok,
            "plugin": "ollama-tools",
            "version": "0.1.0",
            "ollama": ollama_status.model_dump(),
            "memory": memory_stats
        }
    
    @router.get("/models")
    async def get_models():
        """Get the list of available Ollama models."""
        try:
            models = await ollama_client.get_models()
            return {
                "ok": True,
                "models": [model.model_dump() for model in models],
                "count": len(models)
            }
        except Exception as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Failed to fetch models: {str(e)}"
            )
    
    @router.get("/models/{model_name}")
    async def get_model_info(model_name: str):
        """Get detailed information about a specific model."""
        try:
            model_info = await ollama_client.get_model_info(model_name)
            if model_info is None:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Model '{model_name}' not found"
                )
            
            return {
                "ok": True,
                "model": model_info
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch model info: {str(e)}"
            )
    
    @router.post("/route", response_model=RouteResponse)
    async def route_model(request: RouteRequest):
        """Route a prompt to an appropriate model based on criteria."""
        try:
            recommended = await ollama_client.route_model(
                request.prompt, 
                request.criteria
            )
            
            if recommended is None:
                return RouteResponse(
                    ok=False,
                    recommended_model=None,
                    reasoning="No suitable models found"
                )
            
            # Build reasoning string
            reasoning_parts = []
            if len(request.prompt) < 100:
                reasoning_parts.append("short prompt")
            else:
                reasoning_parts.append("long prompt")
            
            if request.criteria:
                reasoning_parts.append(f"criteria: {request.criteria}")
            
            reasoning = f"Selected based on: {', '.join(reasoning_parts)}"
            
            return RouteResponse(
                ok=True,
                recommended_model=recommended,
                reasoning=reasoning
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Routing failed: {str(e)}"
            )
    
    @router.post("/memory/set")
    async def memory_set(request: MemorySetRequest):
        """Set a key-value pair in the memory store."""
        try:
            memory.set(request.key, request.value)
            return {"ok": True, "message": f"Stored '{request.key}'"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store memory: {str(e)}"
            )
    
    @router.get("/memory/get", response_model=MemoryGetResponse)
    async def memory_get(key: str):
        """Get a value from the memory store by key."""
        try:
            value = memory.get(key)
            return MemoryGetResponse(ok=True, value=value)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve memory: {str(e)}"
            )
    
    @router.delete("/memory/delete")
    async def memory_delete(key: str):
        """Delete a key from the memory store."""
        try:
            deleted = memory.delete(key)
            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail=f"Key '{key}' not found"
                )
            return {"ok": True, "message": f"Deleted '{key}'"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete memory: {str(e)}"
            )
    
    @router.get("/memory/list")
    async def memory_list(prefix: str = ""):
        """List all keys in the memory store, optionally filtered by prefix."""
        try:
            keys = memory.list_keys(prefix)
            return {
                "ok": True,
                "keys": keys,
                "count": len(keys),
                "prefix": prefix
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list memory keys: {str(e)}"
            )
    
    @router.get("/memory/stats")
    async def memory_stats():
        """Get statistics about the memory store."""
        try:
            stats = memory.stats()
            return {"ok": True, "stats": stats}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get memory stats: {str(e)}"
            )
    
    # Register the router with the application
    app.include_router(router)
