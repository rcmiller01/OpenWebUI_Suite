"""Plugin registration module for OpenWebUI Plugin Template."""

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""
    ok: bool
    plugin: str
    version: str


def register(app: FastAPI) -> None:
    """Register the template plugin with the FastAPI application.
    
    This function is called by the OpenWebUI extension loader to register
    the plugin routes and functionality.
    
    Args:
        app: The FastAPI application instance to register routes with.
    """
    router = APIRouter(prefix="/ext/template", tags=["owui-template"])
    
    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint for the template plugin.
        
        Returns:
            HealthResponse: Plugin health status and metadata.
        """
        return HealthResponse(
            ok=True,
            plugin="template",
            version="0.1.0"
        )
    
    @router.get("/info")
    async def info() -> dict:
        """Get plugin information and capabilities.
        
        Returns:
            dict: Plugin metadata and feature information.
        """
        return {
            "name": "OpenWebUI Plugin Template",
            "version": "0.1.0",
            "description": "Template for creating OpenWebUI plugins",
            "author": "OpenWebUI Suite",
            "capabilities": [
                "health-check",
                "plugin-info"
            ],
            "endpoints": [
                "/ext/template/health",
                "/ext/template/info"
            ]
        }
    
    # Register the router with the application
    app.include_router(router)
