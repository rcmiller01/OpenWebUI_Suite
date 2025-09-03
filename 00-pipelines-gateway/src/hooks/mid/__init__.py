"""
Mid-processing hooks for pipeline requests

These hooks run during model processing and can modify the request,
add tools, perform real-time analysis, etc.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run_mid_hooks(ctx) -> Any:
    """
    Execute all mid-processing hooks in sequence
    
    Args:
        ctx: PipelineContext object
        
    Returns:
        Modified PipelineContext object
    """
    logger.debug(f"Running mid-hooks for request {ctx.request_id}")
    
    # Tool selection hook
    ctx = await select_tools(ctx)
    
    # Model parameter tuning hook
    ctx = await tune_parameters(ctx)
    
    # Context enrichment hook
    ctx = await enrich_context(ctx)
    
    logger.debug(f"Mid-hooks completed for request {ctx.request_id}")
    return ctx


async def select_tools(ctx) -> Any:
    """
    Select appropriate tools based on intent and content
    """
    logger.debug(f"Selecting tools for request {ctx.request_id}")
    
    available_tools = []
    
    # Tool selection based on intent
    if ctx.intent == "analysis":
        available_tools.extend(["data_analyzer", "code_reviewer"])
    elif ctx.intent == "generation":
        available_tools.extend(["content_generator", "code_generator"])
    elif ctx.intent == "question":
        available_tools.extend(["knowledge_base", "search"])
    
    # Always include basic tools
    available_tools.extend(["calculator", "web_search"])
    
    ctx.metadata["available_tools"] = available_tools
    logger.debug(f"Selected tools: {available_tools}")
    
    return ctx


async def tune_parameters(ctx) -> Any:
    """
    Tune model parameters based on context and user preferences
    """
    logger.debug(f"Tuning parameters for request {ctx.request_id}")
    
    # Adjust temperature based on intent
    if ctx.intent == "analysis":
        ctx.temperature = min(ctx.temperature, 0.3)  # More focused
    elif ctx.intent == "generation":
        ctx.temperature = max(ctx.temperature, 0.7)  # More creative
    
    # Adjust max_tokens based on user preferences
    if ctx.memory and ctx.memory.get("preferences", {}).get("detail_level") == "high":
        if ctx.max_tokens:
            ctx.max_tokens = min(ctx.max_tokens * 2, 4000)
        else:
            ctx.max_tokens = 2000
    
    ctx.metadata["tuned_temperature"] = ctx.temperature
    ctx.metadata["tuned_max_tokens"] = ctx.max_tokens
    
    return ctx


async def enrich_context(ctx) -> Any:
    """
    Enrich context with additional information
    """
    logger.debug(f"Enriching context for request {ctx.request_id}")
    
    # Add system context
    ctx.metadata["system_info"] = {
        "gateway_version": "1.0.0",
        "processing_time": "real-time",
        "capabilities": ["streaming", "tools", "memory"]
    }
    
    # Add user context if available
    if ctx.memory:
        ctx.metadata["user_context"] = {
            "experience_level": "intermediate",  # Based on conversation history
            "preferred_style": ctx.memory.get("preferences", {}).get("style", "helpful")
        }
    
    # Add drive/motivation context (mock)
    ctx.drive = {
        "goal": "assist_user",
        "priority": "accuracy",
        "constraints": ["safety", "truthfulness"]
    }
    
    return ctx
