# gateway/providers/openrouter.py
import os
import time
import requests
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, AsyncIterator
import json
import logging

logger = logging.getLogger(__name__)

# Constants from configuration
MODEL_TOOLCALL = "deepseek/deepseek-chat"
MODEL_VISION = "zhipuai/glm-4v-9b"
MODEL_EXPLICIT = "venice/uncensored:free"
MODEL_CODER = "qwen/qwen-2.5-coder-32b-instruct"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_RETRIES = 3
RETRY_DELAY_MS = 200

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = f"{OPENROUTER_BASE_URL}/chat/completions"
DEFAULT_MODEL = MODEL_TOOLCALL
TIMEOUT_SEC = float(os.getenv("OPENROUTER_TIMEOUT", "60"))

RETRY_STATUSES = {402, 408, 409, 429, 500, 502, 503, 504}

# Model capability mapping
MODEL_CAPABILITIES = {
    MODEL_TOOLCALL: {"tools": True, "vision": False, "streaming": True},
    MODEL_VISION: {"tools": False, "vision": True, "streaming": True},
    MODEL_EXPLICIT: {"tools": False, "vision": False, "streaming": True},
    MODEL_CODER: {"tools": True, "vision": False, "streaming": True}
}


def _headers() -> Dict[str, str]:
    """Get headers for OpenRouter API calls"""
    return {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openwebui-suite.local",
        "X-Title": "OpenWebUI Suite"
    }


def get_model_for_task(task_type: str) -> str:
    """Get the appropriate model for a specific task type"""
    model_map = {
        "toolcall": MODEL_TOOLCALL,
        "vision": MODEL_VISION,
        "explicit": MODEL_EXPLICIT,
        "coding": MODEL_CODER
    }
    return model_map.get(task_type, MODEL_TOOLCALL)


async def chat_stream(messages: List[Dict[str, str]],
                      model: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: int = 1200,
                      tools: Optional[List[Dict]] = None) -> AsyncIterator[str]:
    """
    Streaming chat completion with OpenRouter API
    
    Args:
        messages: List of chat messages
        model: Specific model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        tools: Tool definitions for function calling
        
    Yields:
        Response chunks as they arrive
    """
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    
    model = model or MODEL_TOOLCALL
    
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    if tools and MODEL_CAPABILITIES.get(model, {}).get("tools", False):
        body["tools"] = tools
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            OPENROUTER_URL,
            json=body,
            headers=_headers(),
            timeout=aiohttp.ClientTimeout(total=TIMEOUT_SEC)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(
                    f"OpenRouter API error {response.status}: {error_text}"
                )
            
            async for line in response.content:
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue


def chat(messages: List[Dict[str, str]],
         model_priority: Optional[List[str]] = None,
         temperature: float = 0.7,
         max_tokens: int = 1200,
         tools: Optional[List[Dict]] = None,
         retry_count: int = 0) -> str:
    """
    Call OpenRouter API with model priority fallback and retry logic
    
    Args:
        messages: List of chat messages
        model_priority: List of models to try in order
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        tools: Tool definitions for function calling
        retry_count: Current retry attempt
        
    Returns:
        Generated response text
        
    Raises:
        RuntimeError: If all models fail
    """
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    
    lineup = [m for m in (model_priority or []) if m] or [DEFAULT_MODEL]
    last_err: Any = None
    
    for i, model in enumerate(lineup, 1):
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add tools if model supports them
        if tools and MODEL_CAPABILITIES.get(model, {}).get("tools", False):
            body["tools"] = tools
        
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.post(
                    OPENROUTER_URL,
                    json=body,
                    headers=_headers(),
                    timeout=TIMEOUT_SEC
                )
                
                if r.status_code == 200:
                    j = r.json()
                    return j["choices"][0]["message"]["content"]
                
                # Retry on specific status codes
                if r.status_code in RETRY_STATUSES:
                    last_err = f"{r.status_code} {r.text[:200]}"
                    if attempt < MAX_RETRIES - 1:
                        time.sleep((RETRY_DELAY_MS / 1000) * (2 ** attempt))
                        continue
                else:
                    # Non-retryable error
                    r.raise_for_status()
                    
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep((RETRY_DELAY_MS / 1000) * (2 ** attempt))
                    continue
        
        # Small backoff between model attempts
        time.sleep(0.4)
    
    raise RuntimeError(
        f"OpenRouter call failed after trying {len(lineup)} model(s): "
        f"{last_err}"
    )


def get_model_capabilities(model: str) -> Dict[str, bool]:
    """Get capabilities for a specific model"""
    return MODEL_CAPABILITIES.get(model, {
        "tools": False,
        "vision": False,
        "streaming": False
    })


def check_health() -> Dict[str, Any]:
    """Check OpenRouter API health and model availability"""
    try:
        # Simple test call with minimal tokens
        test_messages = [{"role": "user", "content": "Hi"}]
        chat(test_messages, max_tokens=1)
        
        return {
            "status": "healthy",
            "api_key_configured": bool(OPENROUTER_KEY),
            "test_call_successful": True,
            "default_model": DEFAULT_MODEL,
            "available_models": list(MODEL_CAPABILITIES.keys())
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "api_key_configured": bool(OPENROUTER_KEY),
            "test_call_successful": False,
            "error": str(e),
            "default_model": DEFAULT_MODEL,
            "available_models": list(MODEL_CAPABILITIES.keys())
        }
