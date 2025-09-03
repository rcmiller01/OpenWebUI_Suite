"""
Rule-based classification engine for fast intent detection.

Handles obvious cases with high confidence using pattern matching,
keywords, and heuristics before falling back to ML models.
"""

import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class RuleEngine:
    """Fast rule-based intent classifier"""
    
    def __init__(self):
        """Initialize rule patterns and keywords"""
        self.intent_patterns = self._load_patterns()
        self.confidence_threshold = 0.9  # High threshold for rule-based confidence
        
    def _load_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load classification patterns for each intent"""
        return {
            "emotional": {
                "keywords": [
                    "feel", "feeling", "sad", "happy", "angry", "depressed", "anxious",
                    "worried", "scared", "excited", "lonely", "frustrated", "confused",
                    "love", "hate", "cry", "tears", "heart", "soul", "emotion",
                    "relationship", "boyfriend", "girlfriend", "family", "friend",
                    "support", "help me", "advice", "personal", "therapy", "counseling"
                ],
                "patterns": [
                    r"i feel\s+\w+",
                    r"i am\s+(sad|happy|angry|depressed|anxious|worried)",
                    r"makes? me\s+(feel|sad|happy|angry)",
                    r"my\s+(heart|feelings|emotions?)",
                    r"need\s+(someone|help|support|advice)"
                ],
                "phrases": [
                    "how are you feeling",
                    "i need someone to talk to",
                    "i'm going through",
                    "emotional support",
                    "feeling overwhelmed"
                ]
            },
            
            "technical": {
                "keywords": [
                    "code", "programming", "python", "javascript", "java", "c++", "html",
                    "css", "react", "api", "database", "sql", "algorithm", "function",
                    "class", "method", "variable", "loop", "if", "else", "import",
                    "debug", "error", "exception", "syntax", "compile", "runtime",
                    "framework", "library", "package", "install", "git", "github"
                ],
                "patterns": [
                    r"```[\w]*\n.*?```",  # Code blocks
                    r"`[^`]+`",  # Inline code
                    r"def\s+\w+\(",  # Python function definition
                    r"function\s+\w+\(",  # JavaScript function
                    r"class\s+\w+",  # Class definition
                    r"import\s+\w+",  # Import statements
                    r"from\s+\w+\s+import",  # Python imports
                    r"#include\s*<",  # C++ includes
                    r"<!DOCTYPE|<html|<head|<body",  # HTML
                    r"SELECT|INSERT|UPDATE|DELETE.*FROM",  # SQL
                    r"npm\s+install|pip\s+install",  # Package installation
                ],
                "phrases": [
                    "how do i implement",
                    "write a function",
                    "debug this code",
                    "programming question",
                    "software development"
                ]
            },
            
            "recipes": {
                "keywords": [
                    "recipe", "cook", "cooking", "bake", "baking", "kitchen", "ingredients",
                    "flour", "sugar", "salt", "pepper", "oil", "butter", "eggs", "milk",
                    "oven", "stove", "pan", "pot", "dish", "meal", "food", "eat",
                    "breakfast", "lunch", "dinner", "dessert", "appetizer", "main course",
                    "tablespoon", "teaspoon", "cup", "cups", "minutes", "degrees",
                    "temperature", "heat", "boil", "fry", "grill", "roast", "mix"
                ],
                "patterns": [
                    r"\d+\s*(cups?|tbsp|tsp|tablespoons?|teaspoons?)",
                    r"\d+\s*degrees?",
                    r"\d+\s*minutes?",
                    r"preheat.*oven",
                    r"serves?\s*\d+"
                ],
                "phrases": [
                    "how to cook",
                    "recipe for",
                    "cooking instructions",
                    "baking recipe",
                    "food preparation"
                ]
            },
            
            "finance": {
                "keywords": [
                    "money", "dollar", "dollars", "investment", "invest", "stock", "stocks",
                    "market", "trading", "portfolio", "budget", "budgeting", "savings",
                    "bank", "banking", "loan", "credit", "debt", "mortgage", "insurance",
                    "tax", "taxes", "ira", "401k", "retirement", "pension", "dividend",
                    "interest", "rate", "rates", "bond", "bonds", "mutual fund", "etf",
                    "cryptocurrency", "bitcoin", "ethereum", "price", "cost", "expense"
                ],
                "patterns": [
                    r"\$\d+(?:,\d{3})*(?:\.\d{2})?",  # Dollar amounts
                    r"\d+(?:,\d{3})*\s*dollars?",
                    r"\d+\.?\d*%",  # Percentages
                    r"stock\s+symbol",
                    r"ticker\s+symbol"
                ],
                "phrases": [
                    "financial advice",
                    "investment strategy",
                    "retirement planning",
                    "budget planning",
                    "money management"
                ]
            },
            
            "mm_image": {
                "keywords": [
                    "image", "picture", "photo", "photograph", "visual", "see", "look",
                    "show", "display", "view", "screenshot", "drawing", "diagram",
                    "chart", "graph", "illustration", "art", "design", "color", "pixel"
                ],
                "patterns": [
                    r"what.*in.*image",
                    r"describe.*picture",
                    r"analyze.*photo",
                    r"what.*see"
                ],
                "phrases": [
                    "what is in this image",
                    "describe this picture",
                    "analyze this photo",
                    "what do you see",
                    "image analysis"
                ]
            },
            
            "mm_audio": {
                "keywords": [
                    "audio", "sound", "music", "song", "voice", "speech", "listen",
                    "hear", "recording", "microphone", "speaker", "volume", "bass",
                    "treble", "frequency", "pitch", "tempo", "rhythm", "melody"
                ],
                "patterns": [
                    r"play.*music",
                    r"listen.*to",
                    r"audio.*file",
                    r"sound.*like"
                ],
                "phrases": [
                    "play this audio",
                    "what is this song",
                    "analyze this audio",
                    "transcribe this",
                    "audio processing"
                ]
            }
        }
    
    def classify(
        self, 
        text: str, 
        attachments: Optional[List[Any]] = None,
        last_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify text using rule-based patterns
        
        Returns:
            dict: {
                "intent": str,
                "confidence": float,
                "confident": bool,
                "needs_remote": bool,
                "reasoning": str
            }
        """
        text_lower = text.lower()
        scores = {}
        
        # Check for attachment-based classification first
        if attachments:
            for attachment in attachments:
                if hasattr(attachment, 'type'):
                    attachment_type = attachment.type
                elif isinstance(attachment, dict):
                    attachment_type = attachment.get('type', '')
                else:
                    attachment_type = str(attachment)
                
                if 'image' in attachment_type.lower():
                    return {
                        "intent": "mm_image",
                        "confidence": 0.95,
                        "confident": True,
                        "needs_remote": True,
                        "reasoning": "Image attachment detected"
                    }
                elif 'audio' in attachment_type.lower():
                    return {
                        "intent": "mm_audio", 
                        "confidence": 0.95,
                        "confident": True,
                        "needs_remote": True,
                        "reasoning": "Audio attachment detected"
                    }
        
        # Score each intent based on patterns
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = []
            
            # Keyword matching
            keyword_matches = 0
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    keyword_matches += 1
                    matches.append(f"keyword:{keyword}")
            
            # Pattern matching
            pattern_matches = 0
            for pattern in patterns["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                    pattern_matches += 1
                    matches.append(f"pattern:{pattern[:20]}...")
            
            # Phrase matching  
            phrase_matches = 0
            for phrase in patterns["phrases"]:
                if phrase in text_lower:
                    phrase_matches += 1
                    matches.append(f"phrase:{phrase}")
            
            # Calculate weighted score
            score = (
                keyword_matches * 0.3 +
                pattern_matches * 0.5 + 
                phrase_matches * 0.7
            )
            
            # Normalize by text length (favor shorter, focused text)
            text_words = len(text.split())
            if text_words > 0:
                score = score / (1 + text_words / 20)
            
            scores[intent] = {
                "score": score,
                "matches": matches,
                "keyword_matches": keyword_matches,
                "pattern_matches": pattern_matches,
                "phrase_matches": phrase_matches
            }
        
        # Find best intent
        if not scores:
            return {
                "intent": "general",
                "confidence": 0.1,
                "confident": False,
                "needs_remote": len(text) > 100,
                "reasoning": "No patterns matched"
            }
        
        best_intent = max(scores.keys(), key=lambda x: scores[x]["score"])
        best_score = scores[best_intent]["score"]
        
        # Convert score to confidence (0-1)
        confidence = min(0.95, best_score / 3.0)  # Cap at 0.95
        
        # Consider context from last intent
        if last_intent and last_intent == best_intent:
            confidence += 0.1  # Boost confidence for context continuity
            confidence = min(0.95, confidence)
        
        # Determine if we're confident enough
        confident = confidence >= self.confidence_threshold and best_score > 1.0
        
        # Determine remote processing needs
        needs_remote = self._needs_remote_processing(
            text, best_intent, confidence, attachments
        )
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "confident": confident,
            "needs_remote": needs_remote,
            "reasoning": f"Score: {best_score:.2f}, matches: {len(scores[best_intent]['matches'])}"
        }
    
    def _needs_remote_processing(
        self,
        text: str,
        intent: str,
        confidence: float,
        attachments: Optional[List[Any]] = None
    ) -> bool:
        """Determine if remote processing is needed"""
        
        # Always remote for multimodal
        if intent in ["mm_image", "mm_audio"]:
            return True
        
        # Long text needs remote
        if len(text) > 800:
            return True
        
        # Low confidence suggests complexity
        if confidence < 0.7:
            return True
        
        # Complex technical questions
        if intent == "technical":
            complex_indicators = [
                "implement", "algorithm", "design pattern", "architecture",
                "optimization", "performance", "scalability", "security"
            ]
            if any(indicator in text.lower() for indicator in complex_indicators):
                return True
        
        # Complex financial analysis
        if intent == "finance":
            complex_indicators = [
                "analysis", "strategy", "portfolio", "optimization", 
                "risk assessment", "market analysis"
            ]
            if any(indicator in text.lower() for indicator in complex_indicators):
                return True
        
        return False
