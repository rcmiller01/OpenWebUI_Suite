# gateway/providers/local_fallback.py
import os
import requests
import time
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Local llama.cpp server configuration
LLAMACPP_HOST = os.getenv("LLAMACPP_HOST", "localhost")
LLAMACPP_PORT = os.getenv("LLAMACPP_PORT", "8080")
LLAMACPP_URL = f"http://{LLAMACPP_HOST}:{LLAMACPP_PORT}"
LLAMACPP_TIMEOUT = float(os.getenv("LLAMACPP_TIMEOUT", "30"))

# Default local model
LOCAL_MODEL = "q4_7b.gguf"


def _check_llamacpp_available() -> bool:
    """Check if llama.cpp server is available"""
    try:
        response = requests.get(
            f"{LLAMACPP_URL}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def chat(messages: List[Dict[str, str]],
         temperature: float = 0.7,
         max_tokens: int = 1200) -> str:
    """
    Call local llama.cpp server for offline chat completion
    
    Args:
        messages: List of chat messages
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated response text
        
    Raises:
        RuntimeError: If local server is unavailable
    """
    if not _check_llamacpp_available():
        raise RuntimeError(
            f"Local llama.cpp server not available at {LLAMACPP_URL}"
        )
    
    # Convert messages to prompt format
    prompt = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt += f"System: {content}\n"
        elif role == "user":
            prompt += f"User: {content}\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n"
    
    prompt += "Assistant: "
    
    body = {
        "prompt": prompt,
        "temperature": temperature,
        "n_predict": max_tokens,
        "stop": ["User:", "\n\n"],
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{LLAMACPP_URL}/completion",
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=LLAMACPP_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("content", "").strip()
        else:
            response.raise_for_status()
            return ""  # This line should never be reached
            
    except Exception as e:
        raise RuntimeError(f"Local llama.cpp call failed: {e}")


def get_model_info() -> Dict[str, Any]:
    """Get information about the loaded local model"""
    try:
        if not _check_llamacpp_available():
            return {
                "status": "unavailable",
                "model": LOCAL_MODEL,
                "error": "Server not running"
            }
        
        response = requests.get(
            f"{LLAMACPP_URL}/props",
            timeout=5
        )
        
        if response.status_code == 200:
            props = response.json()
            return {
                "status": "available",
                "model": LOCAL_MODEL,
                "context_length": props.get("n_ctx", "unknown"),
                "total_params": props.get("n_params", "unknown")
            }
        else:
            return {
                "status": "error",
                "model": LOCAL_MODEL,
                "error": f"Status {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "model": LOCAL_MODEL,
            "error": str(e)
        }


def check_health() -> Dict[str, Any]:
    """Check local fallback health"""
    model_info = get_model_info()
    
    return {
        "status": model_info["status"],
        "server_url": LLAMACPP_URL,
        "model": LOCAL_MODEL,
        "available": model_info["status"] == "available",
        "model_info": model_info
    }


def is_available() -> bool:
    """Quick availability check for routing decisions"""
    return _check_llamacpp_available()
