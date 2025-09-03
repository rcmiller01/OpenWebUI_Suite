"""
Post-processing hooks for pipeline requests

These hooks run after model response generation and can modify responses,
log analytics, update memory, etc.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run_post_hooks(ctx) -> Any:
    """
    Execute all post-processing hooks in sequence
    
    Args:
        ctx: PipelineContext object
        
    Returns:
        Modified PipelineContext object
    """
    logger.debug(f"Running post-hooks for request {ctx.request_id}")
    
    # Response filtering hook
    ctx = await filter_response(ctx)
    
    # Analytics logging hook
    ctx = await log_analytics(ctx)
    
    # Memory update hook
    ctx = await update_memory(ctx)
    
    # Feedback collection hook
    ctx = await collect_feedback(ctx)
    
    logger.debug(f"Post-hooks completed for request {ctx.request_id}")
    return ctx


async def filter_response(ctx) -> Any:
    """
    Filter and validate response content
    """
    logger.debug(f"Filtering response for request {ctx.request_id}")
    
    # Check if response exists in metadata
    response = ctx.metadata.get("response")
    if not response:
        return ctx
    
    # Basic content filtering
    if "choices" in response and response["choices"]:
        content = response["choices"][0].get("message", {}).get("content", "")
        
        # Filter potentially harmful content (basic example)
        filtered_words = ["error", "failed", "broken"]  # Simple example
        if any(word in content.lower() for word in filtered_words):
            logger.info(f"Response filtered for request {ctx.request_id}")
            ctx.metadata["response_filtered"] = True
    
    return ctx


async def log_analytics(ctx) -> Any:
    """
    Log analytics and metrics
    """
    logger.debug(f"Logging analytics for request {ctx.request_id}")
    
    # Basic analytics
    analytics = {
        "request_id": ctx.request_id,
        "user_id": ctx.user_id,
        "model": ctx.model,
        "intent": ctx.intent,
        "message_count": len(ctx.messages),
        "temperature": ctx.temperature,
        "stream": ctx.stream,
        "processing_time": ctx.metadata.get("processing_time"),
        "response_length": 0
    }
    
    # Calculate response length if available
    response = ctx.metadata.get("response")
    if response and "choices" in response and response["choices"]:
        content = response["choices"][0].get("message", {}).get("content", "")
        analytics["response_length"] = len(content)
    
    # Log analytics (in production, send to analytics service)
    logger.info(f"Analytics: {analytics}")
    ctx.metadata["analytics"] = analytics
    
    return ctx


async def update_memory(ctx) -> Any:
    """
    Update user memory with conversation data
    """
    logger.debug(f"Updating memory for request {ctx.request_id}")
    
    if not ctx.user_id:
        return ctx  # Skip if no user ID
    
    # Extract topics from conversation
    topics = []
    for message in ctx.messages:
        # Simple topic extraction (in production, use NLP)
        words = message.content.lower().split()
        tech_words = [w for w in words if w in ["python", "fastapi", "ai", "code"]]
        topics.extend(tech_words)
    
    # Update memory (in production, persist to database)
    memory_update = {
        "user_id": ctx.user_id,
        "topics": list(set(topics)),
        "last_intent": ctx.intent,
        "conversation_count": ctx.memory.get("conversation_count", 0) + 1,
        "timestamp": ctx.metadata.get("timestamp")
    }
    
    logger.debug(f"Memory update: {memory_update}")
    ctx.metadata["memory_update"] = memory_update
    
    return ctx


async def collect_feedback(ctx) -> Any:
    """
    Collect implicit feedback signals
    """
    logger.debug(f"Collecting feedback for request {ctx.request_id}")
    
    # Implicit feedback signals
    feedback = {
        "request_id": ctx.request_id,
        "response_quality": "unknown",  # Would be determined by user actions
        "user_satisfaction": "pending",
        "technical_success": True,  # Request completed successfully
        "content_filtered": ctx.metadata.get("response_filtered", False)
    }
    
    # In production, this would set up mechanisms to collect
    # explicit feedback from users later
    
    ctx.metadata["feedback"] = feedback
    
    return ctx
