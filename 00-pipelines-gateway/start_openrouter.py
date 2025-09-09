#!/usr/bin/env python3
"""
Enhanced startup script for OpenRouter Gateway integration
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Add src to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="OpenRouter Gateway",
        description="OpenRouter-first LLM gateway with intelligent routing",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "openrouter-gateway"}
    
    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}
    
    # Include OpenRouter Gateway routes
    try:
        from src.api.openrouter_gateway import router as openrouter_router
        app.include_router(openrouter_router)
        logger.info("✅ OpenRouter Gateway routes loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load OpenRouter Gateway routes: {e}")
        # Continue without OpenRouter routes for basic health checks
    
    # Legacy gateway routes for backward compatibility
    try:
        from src.router.providers import get_model_router
        
        @app.post("/chat/completions")
        async def legacy_chat_completions(request: dict):
            """Legacy endpoint for backward compatibility"""
            logger.warning("Using legacy chat completions endpoint")
            # Redirect to new OpenRouter endpoint
            from src.api.openrouter_gateway import chat_completions
            from src.api.openrouter_gateway import ChatRequest
            from fastapi import BackgroundTasks
            
            # Convert dict to ChatRequest
            chat_request = ChatRequest(**request)
            background_tasks = BackgroundTasks()
            
            return await chat_completions(chat_request, background_tasks)
            
        logger.info("✅ Legacy gateway routes loaded")
    except Exception as e:
        logger.warning(f"⚠️ Legacy routes not available: {e}")
    
    return app

def main():
    """Main entry point"""
    # Environment configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    # Log configuration
    logger.info("🚀 Starting OpenRouter Gateway")
    logger.info(f"📡 Host: {host}:{port}")
    logger.info(f"🔄 Reload: {reload}")
    
    # Environment checks
    if os.getenv("OPENROUTER_API_KEY"):
        logger.info("✅ OpenRouter API key configured")
    else:
        logger.warning("⚠️ OpenRouter API key not configured")
    
    if os.getenv("LLAMACPP_HOST"):
        logger.info(f"🖥️ Local fallback: {os.getenv('LLAMACPP_HOST')}:{os.getenv('LLAMACPP_PORT', '8080')}")
    else:
        logger.info("💻 Local fallback: localhost:8080 (default)")
    
    # Create and run application
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
