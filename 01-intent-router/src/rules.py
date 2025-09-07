"""
Family-based classification engine with model priority routing.

Routes user inputs based on content family (TECH, LEGAL, REGULATED, etc.)
and provides emotion template and provider recommendations.
"""

import os
import re
import time
import logging
from typing import Literal, Tuple, Dict, List, Optional, Any

logger = logging.getLogger(__name__)

Family = Literal["TECH", "LEGAL", "REGULATED", "PSYCHOTHERAPY",
                 "GENERAL_PRECISION", "OPEN_ENDED"]

# --- Regex buckets (expandable) ---
TECH_RX = re.compile(r"\b(code|bug|stacktrace|exception|sql|regex|docker|kubernetes|api|typescript|python|compile|error)\b", re.I)
LEGAL_RX = re.compile(r"\b(contract|nda|terms|tort|statute|indemnif(y|ication)|warranty|governing law)\b", re.I)
REG_RX = re.compile(
    r"\b("
    r"pci[\s-]?dss|sox|hipaa|hitech|ferpa|coppa|glba|fisma|fedramp|nist\s*800-53|nist\s*csf|iso[\s/:-]*27\d{2}"
    r"|gdpr|ccpa|cpra|mifid|basel\s*iii|aml|kyc|psd2|eidas|cfpb|ofac|itar|ear|faa|fda|sec\b"
    r")\b", re.I
)
PSY_RX = re.compile(r"\b(therapy|therapist|counsel(or|ing)|anxiety|panic|depress(ed|ion)?|grief|trauma|cope|mental health|feelings)\b", re.I)


def classify(text: str) -> Family:
    """Classify text into content family with precedence order"""
    t = text[:4000]
    # precedence: PSY > REG > LEGAL > TECH > PRECISION > OPEN_ENDED
    if PSY_RX.search(t):
        return "PSYCHOTHERAPY"
    if REG_RX.search(t):
        return "REGULATED"
    if LEGAL_RX.search(t):
        return "LEGAL"
    if TECH_RX.search(t):
        return "TECH"
    if re.search(r"\b(prove|derive|exact|step[- ]?by[- ]?step|check|verify|confidence)\b", t, re.I):
        return "GENERAL_PRECISION"
    return "OPEN_ENDED"


# --- Model priorities (OpenRouter) ---
def _env_list(name: str, default: List[str]) -> List[str]:
    """Parse comma-separated environment variable into list"""
    v = os.getenv(name, "")
    return default if not v.strip() else [x.strip() for x in v.split(",") if x.strip()]


# Replace slugs with the exact ones in your OpenRouter account
GPT_4O = "openai/gpt-4o"
GPT_4O_MINI = "openai/gpt-4o-mini"
CLAUDE_SONNET = "anthropic/claude-3-5-sonnet-20241022"
QWEN_72B = "qwen/qwen-2.5-72b-instruct"
LLAMA_70B = "meta-llama/llama-3.1-70b-instruct"

DEFAULT_OR_PRIORITY = [GPT_4O_MINI, CLAUDE_SONNET, GPT_4O, LLAMA_70B, QWEN_72B]
FAMILY_PRIORITIES: Dict[Family, List[str]] = {
    "TECH": _env_list("OPENROUTER_PRIORITIES_TECH", DEFAULT_OR_PRIORITY),
    "LEGAL": _env_list("OPENROUTER_PRIORITIES_LEGAL", DEFAULT_OR_PRIORITY),
    "PSYCHOTHERAPY": _env_list("OPENROUTER_PRIORITIES_PSYCHOTHERAPY", DEFAULT_OR_PRIORITY),
    "REGULATED": _env_list("OPENROUTER_PRIORITIES_REGULATED", DEFAULT_OR_PRIORITY),
    "GENERAL_PRECISION": [],
    "OPEN_ENDED": [],
}

ALLOW_EXTERNAL_FOR_REGULATED = os.getenv("ALLOW_EXTERNAL_FOR_REGULATED", "0") == "1"


def policy_for_family(f: Family) -> Tuple[str, str]:
    """Map family -> (emotion_template_id, provider)"""
    if f == "TECH":
        return ("none", "openrouter")
    if f == "LEGAL":
        return ("none", "openrouter")
    if f == "PSYCHOTHERAPY":
        return ("empathy_therapist", "openrouter")
    if f == "GENERAL_PRECISION":
        return ("self_monitor", "local")
    if f == "OPEN_ENDED":
        return ("stakes", "local")
    if f == "REGULATED":
        return ("none", "openrouter" if ALLOW_EXTERNAL_FOR_REGULATED else "local")
    return ("stakes", "local")


def build_route(user_text: str, tags_in=None):
    """Build routing decision based on user text and optional tags"""
    family = classify(user_text)
    tpl, provider = policy_for_family(family)
    tags = list(tags_in or [])
    
    if family in ("TECH", "LEGAL", "REGULATED") and "no_emotion" not in tags:
        tags.append("no_emotion")
    if family == "PSYCHOTHERAPY" and "psychotherapy" not in tags:
        tags.append("psychotherapy")
    
    return {
        "family": family,
        "emotion_template_id": tpl,
        "provider": provider,
        "openrouter_model_priority": FAMILY_PRIORITIES.get(family, []),
        "tags": tags
    }


class RuleEngine:
    """Family-based classification and routing engine"""
    
    def __init__(self):
        """Initialize rule patterns and keywords"""
        self.confidence_threshold = 0.9  # High threshold for rule-based confidence
        logger.info("Initialized family-based rule engine")
        
    def classify(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Classify input text and return routing information"""
        start_time = time.time()
        
        # Get family classification and routing info
        route_info = build_route(text, context.get("tags") if context else None)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Map family to intent for backward compatibility
        family_to_intent = {
            "TECH": "technical",
            "LEGAL": "legal", 
            "REGULATED": "compliance",
            "PSYCHOTHERAPY": "emotional",
            "GENERAL_PRECISION": "analytical",
            "OPEN_ENDED": "general"
        }
        
        intent = family_to_intent.get(route_info["family"], "general")
        
        # Determine if remote processing is needed
        needs_remote = route_info["provider"] == "openrouter"
        
        return {
            "intent": intent,
            "family": route_info["family"],
            "emotion_template_id": route_info["emotion_template_id"],
            "provider": route_info["provider"],
            "openrouter_model_priority": route_info["openrouter_model_priority"],
            "tags": route_info["tags"],
            "confidence": self.confidence_threshold,
            "needs_remote": needs_remote,
            "processing_time_ms": processing_time,
            "reasoning": f"Family: {route_info['family']}, Provider: {route_info['provider']}, Template: {route_info['emotion_template_id']}"
        }
