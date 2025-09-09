# 00-pipelines-gateway/src/api/openrouter_gateway.py
"""
Main OpenRouter Gateway API
Integrates routing policy, providers, tools, and memory
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime

from ..router.policy import get_router_policy
from ..providers import openrouter, local_fallback
from ..tools.dispatch import get_tool_dispatcher, dispatch_tool_calls
from ..memory.integration import store_conversation_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["openrouter-gateway"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1200
    tools: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    id: str
    model: str
    provider: str
    content: str
    usage: Dict[str, int]
    conversation_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Main chat completions endpoint with OpenRouter-first routing
    """
    # Generate response ID and conversation ID if needed
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    conversation_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
    
    # Convert Pydantic models to dicts
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    try:
        # Get routing policy and determine provider/model
        policy = get_router_policy()
        provider, model = policy.route_request(
            messages, 
            request.tools, 
            request.model
        )
        
        logger.info(f"Routing to {provider} with model {model}")
        
        # Execute the request based on provider
        if provider == "openrouter":
            content = await _execute_openrouter_request(
                messages, model, request.temperature, request.max_tokens, request.tools
            )
        elif provider == "local_fallback":
            content = await _execute_local_request(
                messages, request.temperature, request.max_tokens
            )
        else:
            raise HTTPException(status_code=500, detail=f"Unknown provider: {provider}")
        
        # Handle tool calls if present in response
        tool_calls = None
        if request.tools and "tool_calls" in content:
            tool_calls = content.get("tool_calls", [])
            if tool_calls:
                # Execute tool calls
                async with get_tool_dispatcher() as dispatcher:
                    tool_results = await dispatch_tool_calls(tool_calls)
                    # Add tool results to response metadata
                    content["tool_results"] = tool_results
        
        # Extract final content
        final_content = content if isinstance(content, str) else content.get("content", str(content))
        
        # Create response
        response = ChatResponse(
            id=response_id,
            model=model,
            provider=provider,
            content=final_content,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},  # Placeholder
            conversation_id=conversation_id,
            tool_calls=tool_calls
        )
        
        # Store conversation in background
        background_tasks.add_task(
            _store_conversation_background,
            conversation_id,
            messages + [{"role": "assistant", "content": final_content}],
            f"{provider}:{model}",
            {"response_id": response_id, "tool_calls": tool_calls}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        
        # Try fallback if primary provider failed
        policy = get_router_policy()
        fallback = policy.get_fallback_strategy(provider, e)
        
        if fallback:
            fallback_provider, fallback_model = fallback
            try:
                logger.info(f"Trying fallback: {fallback_provider} with {fallback_model}")
                
                if fallback_provider == "local_fallback":
                    content = await _execute_local_request(
                        messages, request.temperature, request.max_tokens
                    )
                    
                    response = ChatResponse(
                        id=response_id,
                        model=fallback_model,
                        provider=fallback_provider,
                        content=content,
                        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        conversation_id=conversation_id
                    )
                    
                    # Store fallback conversation
                    background_tasks.add_task(
                        _store_conversation_background,
                        conversation_id,
                        messages + [{"role": "assistant", "content": content}],
                        f"{fallback_provider}:{fallback_model}",
                        {"response_id": response_id, "fallback": True, "original_error": str(e)}
                    )
                    
                    return response
                    
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
        
        raise HTTPException(status_code=500, detail=f"All providers failed: {e}")


async def _execute_openrouter_request(messages: List[Dict[str, str]],
                                     model: str,
                                     temperature: float,
                                     max_tokens: int,
                                     tools: Optional[List[Dict[str, Any]]] = None) -> str:
    """Execute request using OpenRouter provider"""
    return openrouter.chat(
        messages=messages,
        model_priority=[model],
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools
    )


async def _execute_local_request(messages: List[Dict[str, str]],
                                temperature: float,
                                max_tokens: int) -> str:
    """Execute request using local fallback provider"""
    return local_fallback.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )


async def _store_conversation_background(conversation_id: str,
                                       messages: List[Dict[str, Any]],
                                       model_used: str,
                                       metadata: Dict[str, Any]):
    """Background task to store conversation in memory"""
    try:
        await store_conversation_async(conversation_id, messages, model_used, metadata)
    except Exception as e:
        logger.error(f"Failed to store conversation {conversation_id}: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    policy = get_router_policy()
    
    # Check provider health
    openrouter_health = openrouter.check_health()
    local_health = local_fallback.check_health()
    
    # Check tools health
    async with get_tool_dispatcher() as dispatcher:
        tools_health = await dispatcher.health_check()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "routing": policy.get_routing_status(),
        "providers": {
            "openrouter": openrouter_health,
            "local_fallback": local_health
        },
        "tools": tools_health
    }


@router.get("/models")
async def list_models():
    """List available models"""
    return {
        "openrouter": list(openrouter.MODEL_CAPABILITIES.keys()),
        "local_fallback": ["q4_7b.gguf"],
        "routing_policy": "openrouter_first_with_local_fallback"
    }


@router.get("/routing/status")
async def routing_status():
    """Get current routing status"""
    policy = get_router_policy()
    return policy.get_routing_status()


@router.post("/routing/refresh")
async def refresh_routing():
    """Refresh routing policy (re-check provider availability)"""
    from ..router.policy import refresh_policy
    policy = refresh_policy()
    return {
        "status": "refreshed",
        "routing": policy.get_routing_status()
    }
