"""
Pre-processing hooks for pipeline requests

These hooks run before the main model processing and can modify
the request context, add authentication, perform input validation, etc.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def run_pre_hooks(ctx) -> Any:
    """
    Execute all pre-processing hooks in sequence
    
    Args:
        ctx: PipelineContext object
        
    Returns:
        Modified PipelineContext object
    """
    logger.debug(f"Running pre-hooks for request {ctx.request_id}")
    
    # Authentication hook
    ctx = await authenticate_user(ctx)
    
    # Input validation hook
    ctx = await validate_input(ctx)
    
    # Intent detection hook
    ctx = await detect_intent(ctx)
    
    # Memory loading hook
    ctx = await load_user_memory(ctx)
    
    logger.debug(f"Pre-hooks completed for request {ctx.request_id}")
    return ctx


async def authenticate_user(ctx) -> Any:
    """
    Authenticate user and set permissions
    """
    logger.debug(f"Authenticating user for request {ctx.request_id}")
    
    # Mock authentication - in production would validate tokens, etc.
    if ctx.user_id:
        ctx.metadata["authenticated"] = True
        ctx.metadata["permissions"] = ["chat", "tools"]
    else:
        ctx.metadata["authenticated"] = False
        ctx.metadata["permissions"] = ["chat"]  # Limited permissions
    
    return ctx


async def validate_input(ctx) -> Any:
    """
    Validate and sanitize input messages
    """
    logger.debug(f"Validating input for request {ctx.request_id}")
    
    # Basic validation
    if not ctx.messages:
        raise ValueError("No messages provided")
    
    # Content length validation
    total_length = sum(len(msg.content) for msg in ctx.messages)
    if total_length > 100000:  # 100k character limit
        raise ValueError("Input too long")
    
    # Content filtering (basic example)
    for msg in ctx.messages:
        if any(word in msg.content.lower() for word in ["spam", "abuse"]):
            logger.warning(f"Potentially problematic content in {ctx.request_id}")
            ctx.metadata["content_warning"] = True
    
    ctx.metadata["input_validated"] = True
    return ctx


async def detect_intent(ctx) -> Any:
    """
    Detect user intent from messages
    """
    logger.debug(f"Detecting intent for request {ctx.request_id}")
    
    # Simple intent detection based on keywords
    last_message = ctx.messages[-1].content.lower() if ctx.messages else ""
    
    if any(word in last_message for word in ["help", "how", "what", "?"]):
        ctx.intent = "question"
    elif any(word in last_message for word in ["create", "generate", "make"]):
        ctx.intent = "generation"
    elif any(word in last_message for word in ["analyze", "review", "check"]):
        ctx.intent = "analysis"
    else:
        ctx.intent = "general"
    
    logger.debug(f"Detected intent '{ctx.intent}' for request {ctx.request_id}")
    return ctx


async def load_user_memory(ctx) -> Any:
    """
    Load user memory and conversation history
    """
    logger.debug(f"Loading memory for request {ctx.request_id}")
    
    # Mock memory loading - in production would query database
    if ctx.user_id:
        ctx.memory = {
            "conversation_count": 42,
            "last_topics": ["python", "fastapi", "ai"],
            "preferences": {
                "style": "helpful",
                "detail_level": "medium"
            }
        }
    else:
        ctx.memory = {
            "conversation_count": 0,
            "last_topics": [],
            "preferences": {}
        }
    
    return ctx
