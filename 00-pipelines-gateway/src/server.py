"""
OpenAI-compatible Pipelines Gateway Server

A central server that provides OpenAI-compatible chat completions with
a plugin architecture for pre/mid/post processing hooks.
"""

import json
import logging
import os
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .hooks.pre import run_pre_hooks
from .hooks.mid import run_mid_hooks
from .hooks.post import run_post_hooks
from .router.model_map import ModelRouter
from .tools.registry import ToolRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="OpenWebUI Pipelines Gateway",
    description="OpenAI-compatible chat completions with plugin hooks",
    version="1.0.0"
)

# Global state
model_router: Optional[ModelRouter] = None
tool_registry: Optional[ToolRegistry] = None


class ChatMessage(BaseModel):
    """OpenAI chat message format"""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Name of the message author")


class ChatCompletionRequest(BaseModel):
    """OpenAI chat completion request format"""
    model: str = Field(..., description="Model to use for completion")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream responses")
    user: Optional[str] = Field(None, description="User identifier")


class PipelineContext(BaseModel):
    """Internal context passed through pipeline hooks"""
    user_id: Optional[str] = None
    request_id: str
    messages: List[ChatMessage]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    intent: Optional[str] = None
    memory: Optional[Dict[str, Any]] = None
    affect: Optional[Dict[str, Any]] = None
    drive: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatCompletionChunk(BaseModel):
    """OpenAI streaming response chunk"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global model_router, tool_registry
    
    logger.info("Starting OpenWebUI Pipelines Gateway...")
    
    # Load configurations
    try:
        model_router = ModelRouter()
        await model_router.load_config()
        logger.info("Model router initialized")
        
        tool_registry = ToolRegistry()
        await tool_registry.load_config()
        logger.info("Tool registry initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    logger.info("Pipelines Gateway started successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "model_router": model_router is not None,
            "tool_registry": tool_registry is not None
        }
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, http_request: Request):
    """
    OpenAI-compatible chat completions endpoint with pipeline hooks
    """
    request_id = f"req_{int(time.time() * 1000)}"
    
    # Create pipeline context
    ctx = PipelineContext(
        user_id=request.user,
        request_id=request_id,
        messages=request.messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
        metadata={
            "client_ip": http_request.client.host if http_request.client else None,
            "user_agent": http_request.headers.get("user-agent"),
            "timestamp": time.time()
        }
    )
    
    logger.info(f"Processing chat completion request {request_id}")
    
    try:
        # Pre-processing hooks
        ctx = await run_pre_hooks(ctx)
        logger.debug(f"Pre-hooks completed for {request_id}")
        
        # Route to appropriate model
        if not model_router:
            raise HTTPException(status_code=500, detail="Model router not initialized")
        
        routed_model = await model_router.route_model(ctx.model, ctx)
        ctx.model = routed_model
        
        # Mid-processing hooks
        ctx = await run_mid_hooks(ctx)
        logger.debug(f"Mid-hooks completed for {request_id}")
        
        # Generate response
        if ctx.stream:
            return StreamingResponse(
                stream_chat_completion(ctx),
                media_type="text/plain"
            )
        else:
            return await generate_chat_completion(ctx)
            
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def stream_chat_completion(ctx: PipelineContext) -> AsyncGenerator[str, None]:
    """Generate streaming chat completion response"""
    try:
        # Mock streaming response for development
        # In production, this would call the actual model
        response_text = "This is a mock streaming response from the Pipelines Gateway. "
        
        chunk_id = f"chatcmpl-{ctx.request_id}"
        created = int(time.time())
        
        # Stream response in chunks
        words = response_text.split()
        for i, word in enumerate(words):
            chunk = ChatCompletionChunk(
                id=chunk_id,
                created=created,
                model=ctx.model,
                choices=[{
                    "index": 0,
                    "delta": {
                        "content": word + " " if i < len(words) - 1 else word
                    },
                    "finish_reason": None
                }]
            )
            
            yield f"data: {chunk.model_dump_json()}\n\n"
            
            # Small delay to simulate streaming
            await asyncio.sleep(0.1)
        
        # Final chunk with finish_reason
        final_chunk = ChatCompletionChunk(
            id=chunk_id,
            created=created,
            model=ctx.model,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        )
        
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
        # Post-processing hooks (after streaming)
        await run_post_hooks(ctx)
        
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


async def generate_chat_completion(ctx: PipelineContext) -> Dict[str, Any]:
    """Generate non-streaming chat completion response"""
    try:
        # Mock response for development
        # In production, this would call the actual model
        response_text = "This is a mock response from the Pipelines Gateway."
        
        response = {
            "id": f"chatcmpl-{ctx.request_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": ctx.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": sum(len(msg.content.split()) for msg in ctx.messages),
                "completion_tokens": len(response_text.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in ctx.messages) + len(response_text.split())
            }
        }
        
        # Post-processing hooks
        ctx.metadata["response"] = response
        await run_post_hooks(ctx)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating completion: {e}")
        raise


@app.get("/v1/models")
async def list_models():
    """List available models"""
    if not model_router:
        raise HTTPException(status_code=500, detail="Model router not initialized")
    
    models = await model_router.list_models()
    return {
        "object": "list",
        "data": models
    }


@app.get("/v1/tools")
async def list_tools():
    """List available tools"""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    tools = await tool_registry.list_tools()
    return {
        "object": "list",
        "data": tools
    }


# Import asyncio at the top level for streaming
import asyncio


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8088,
        reload=True,
        log_level="info"
    )
