# gateway/providers/openrouter.py
import os
import time
import requests
from typing import List, Dict, Any

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1/chat/completions")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL_DEFAULT", "openai/gpt-4o-mini")
TIMEOUT_SEC = float(os.getenv("OPENROUTER_TIMEOUT", "60"))

RETRY_STATUSES = {402, 408, 409, 429, 500, 502, 503, 504}


def _headers() -> Dict[str, str]:
    """Get headers for OpenRouter API calls"""
    return {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }


def chat(messages: List[Dict[str, str]],
         model_priority: List[str] = None,
         temperature: float = 0.7,
         max_tokens: int = 1200) -> str:
    """
    Call OpenRouter API with model priority fallback
    
    Args:
        messages: List of chat messages
        model_priority: List of models to try in order
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated response text
        
    Raises:
        RuntimeError: If all models fail
    """
    lineup = [m for m in (model_priority or []) if m] or [DEFAULT_MODEL]
    last_err: Any = None
    
    for i, model in enumerate(lineup, 1):
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
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
            
            # retry on throttling/payment/5xx; fall through to next model
            if r.status_code in RETRY_STATUSES:
                last_err = f"{r.status_code} {r.text[:200]}"
            else:
                # non-retryable error; surface
                r.raise_for_status()
                
        except Exception as e:
            last_err = e
            
        # small backoff between tries
        time.sleep(0.4)
    
    raise RuntimeError(f"OpenRouter call failed after trying {len(lineup)} model(s): {last_err}")


def check_health() -> Dict[str, Any]:
    """Check OpenRouter API health and model availability"""
    try:
        # Simple test call with minimal tokens
        test_messages = [{"role": "user", "content": "Hi"}]
        response = chat(test_messages, max_tokens=1)
        
        return {
            "status": "healthy",
            "api_key_configured": bool(OPENROUTER_KEY),
            "test_call_successful": True,
            "default_model": DEFAULT_MODEL
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "api_key_configured": bool(OPENROUTER_KEY),
            "test_call_successful": False,
            "error": str(e),
            "default_model": DEFAULT_MODEL
        }
