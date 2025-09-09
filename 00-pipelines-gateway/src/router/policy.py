# 00-pipelines-gateway/src/router/policy.py
"""
OpenRouter-first routing policy with intelligent fallback handling
"""
import os
import re
from typing import Dict, Any, List, Optional, Tuple
import logging
from ..providers import openrouter, local_fallback

logger = logging.getLogger(__name__)

# Content analysis patterns
EXPLICIT_PATTERNS = [
    r'\b(sex|sexual|porn|xxx|nude|explicit|nsfw)\b',
    r'\b(erotic|sensual|intimate|seductive)\b',
    r'\b(fetish|bdsm|kinky|adult content)\b'
]

VISION_PATTERNS = [
    r'\b(image|photo|picture|visual|diagram)\b',
    r'\b(see|look|view|analyze.*image)\b',
    r'\b(what.*in.*image|describe.*image)\b'
]

CODING_PATTERNS = [
    r'\b(code|programming|debug|function|class)\b',
    r'\b(python|javascript|typescript|java|c\+\+)\b',
    r'\b(algorithm|implementation|refactor)\b',
    r'\b(github|repository|commit|pull request)\b'
]

TOOL_PATTERNS = [
    r'\b(call|invoke|execute|run).*\b(tool|function|api)\b',
    r'\b(search|lookup|find|fetch)\b',
    r'\b(calculate|compute|analyze|process)\b'
]


class RouterPolicy:
    """Intelligent routing policy for OpenRouter-first architecture"""
    
    def __init__(self):
        self.openrouter_available = self._check_openrouter()
        self.local_available = local_fallback.is_available()
        
    def _check_openrouter(self) -> bool:
        """Check if OpenRouter is available"""
        try:
            health = openrouter.check_health()
            return health.get("status") == "healthy"
        except Exception:
            return False
    
    def _analyze_content(self, messages: List[Dict[str, str]]) -> Dict[str, bool]:
        """Analyze message content for routing hints"""
        combined_text = " ".join([
            msg.get("content", "").lower() 
            for msg in messages 
            if msg.get("content")
        ])
        
        return {
            "explicit": any(re.search(pattern, combined_text, re.IGNORECASE) 
                          for pattern in EXPLICIT_PATTERNS),
            "vision": any(re.search(pattern, combined_text, re.IGNORECASE) 
                        for pattern in VISION_PATTERNS),
            "coding": any(re.search(pattern, combined_text, re.IGNORECASE) 
                        for pattern in CODING_PATTERNS),
            "tools": any(re.search(pattern, combined_text, re.IGNORECASE) 
                       for pattern in TOOL_PATTERNS)
        }
    
    def _has_images(self, messages: List[Dict[str, str]]) -> bool:
        """Check if messages contain image data"""
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
        return False
    
    def route_request(self, 
                     messages: List[Dict[str, str]], 
                     tools: Optional[List[Dict]] = None,
                     force_model: Optional[str] = None) -> Tuple[str, str]:
        """
        Determine routing strategy for a request
        
        Args:
            messages: Chat messages
            tools: Tool definitions if any
            force_model: Override model selection
            
        Returns:
            Tuple of (provider, model) where provider is 
            'openrouter' or 'local_fallback'
        """
        # Force model override
        if force_model:
            if force_model.startswith("local/"):
                return ("local_fallback", force_model.replace("local/", ""))
            else:
                return ("openrouter", force_model)
        
        # Check for local-only mode
        if not self.openrouter_available:
            if self.local_available:
                logger.warning("OpenRouter unavailable, falling back to local")
                return ("local_fallback", "q4_7b.gguf")
            else:
                raise RuntimeError(
                    "No available providers: OpenRouter unavailable and "
                    "local fallback not running"
                )
        
        # Analyze content for routing hints
        content_analysis = self._analyze_content(messages)
        has_images = self._has_images(messages)
        has_tools = bool(tools)
        
        # Route based on content and capabilities
        if has_images or content_analysis["vision"]:
            return ("openrouter", openrouter.MODEL_VISION)
        
        elif content_analysis["explicit"]:
            return ("openrouter", openrouter.MODEL_EXPLICIT)
        
        elif content_analysis["coding"]:
            return ("openrouter", openrouter.MODEL_CODER)
        
        elif has_tools or content_analysis["tools"]:
            return ("openrouter", openrouter.MODEL_TOOLCALL)
        
        else:
            # Default to primary model
            return ("openrouter", openrouter.MODEL_TOOLCALL)
    
    def get_fallback_strategy(self, 
                            primary_provider: str, 
                            error: Exception) -> Optional[Tuple[str, str]]:
        """
        Determine fallback strategy when primary provider fails
        
        Args:
            primary_provider: The provider that failed
            error: The error that occurred
            
        Returns:
            Tuple of (provider, model) for fallback, or None if no fallback
        """
        error_str = str(error).lower()
        
        # If OpenRouter failed, try local fallback
        if primary_provider == "openrouter":
            if self.local_available:
                logger.warning(f"OpenRouter failed ({error}), using local fallback")
                return ("local_fallback", "q4_7b.gguf")
            else:
                logger.error("OpenRouter failed and no local fallback available")
                return None
        
        # If local failed, no fallback strategy
        elif primary_provider == "local_fallback":
            logger.error("Local fallback failed, no further options")
            return None
        
        return None
    
    def get_routing_status(self) -> Dict[str, Any]:
        """Get current routing status and provider availability"""
        return {
            "openrouter": {
                "available": self.openrouter_available,
                "models": list(openrouter.MODEL_CAPABILITIES.keys()) if self.openrouter_available else []
            },
            "local_fallback": {
                "available": self.local_available,
                "model": "q4_7b.gguf" if self.local_available else None
            },
            "routing_enabled": self.openrouter_available or self.local_available,
            "fallback_available": self.local_available
        }


# Global router policy instance
_router_policy = None


def get_router_policy() -> RouterPolicy:
    """Get or create the global router policy instance"""
    global _router_policy
    if _router_policy is None:
        _router_policy = RouterPolicy()
    return _router_policy


def refresh_policy() -> RouterPolicy:
    """Refresh the router policy (re-check provider availability)"""
    global _router_policy
    _router_policy = RouterPolicy()
    return _router_policy
