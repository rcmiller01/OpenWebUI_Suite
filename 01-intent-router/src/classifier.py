"""
Lightweight ML classifier for intent detection.

Falls back to simple keyword-based classification if no model is available.
Designed to be fast and lightweight (<50MB total).
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
import json
import os

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Lightweight ML-based intent classifier"""
    
    def __init__(self):
        """Initialize classifier"""
        self.model = None
        self.vectorizer = None
        self.intents = [
            "emotional", "technical", "recipes", "finance", 
            "mm_image", "mm_audio", "general"
        ]
        
        # Fallback keyword-based classifier
        self.keyword_classifier = self._build_keyword_classifier()
        
    async def load_model(self):
        """Load ML model if available, otherwise use keyword fallback"""
        model_path = os.path.join(os.path.dirname(__file__), "model.bin")
        
        if os.path.exists(model_path):
            try:
                logger.info("Loading ML model...")
                # In a real implementation, you might load:
                # - A small BERT model
                # - TF-IDF + Logistic Regression 
                # - FastText embeddings
                # - Custom lightweight transformer
                
                # For now, we'll use the keyword classifier
                logger.info("Model loading not implemented, using keyword fallback")
                self.model = None
                
            except Exception as e:
                logger.warning(f"Failed to load model: {e}, using keyword fallback")
                self.model = None
        else:
            logger.info("No model file found, using keyword fallback")
            self.model = None
    
    async def classify(
        self,
        text: str,
        attachments: Optional[List[Any]] = None,
        last_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify text using ML model or keyword fallback
        
        Returns:
            dict: {
                "intent": str,
                "confidence": float,
                "reasoning": str
            }
        """
        
        # Handle attachments first
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
                        "reasoning": "Image attachment detected"
                    }
                elif 'audio' in attachment_type.lower():
                    return {
                        "intent": "mm_audio",
                        "confidence": 0.95, 
                        "reasoning": "Audio attachment detected"
                    }
        
        if self.model is not None:
            # Use ML model (not implemented in this version)
            return await self._ml_classify(text, last_intent)
        else:
            # Use keyword-based fallback
            return self._keyword_classify(text, last_intent)
    
    async def _ml_classify(self, text: str, last_intent: Optional[str]) -> Dict[str, Any]:
        """ML-based classification (placeholder for future implementation)"""
        
        # Simulate async processing
        await asyncio.sleep(0.001)
        
        # This would contain actual ML inference:
        # 1. Tokenize and encode text
        # 2. Run through model
        # 3. Get probability distribution
        # 4. Return best intent with confidence
        
        # For now, fall back to keyword classifier
        return self._keyword_classify(text, last_intent)
    
    def _keyword_classify(self, text: str, last_intent: Optional[str]) -> Dict[str, Any]:
        """Keyword-based classification fallback"""
        
        text_lower = text.lower()
        scores = {}
        
        # Score each intent
        for intent, keywords in self.keyword_classifier.items():
            score = 0
            matches = []
            
            for keyword, weight in keywords.items():
                count = text_lower.count(keyword)
                if count > 0:
                    score += count * weight
                    matches.append(keyword)
            
            scores[intent] = {
                "score": score,
                "matches": matches
            }
        
        # Find best intent
        if not any(scores[intent]["score"] > 0 for intent in scores):
            return {
                "intent": "general",
                "confidence": 0.3,
                "reasoning": "No keywords matched, defaulting to general"
            }
        
        best_intent = max(scores.keys(), key=lambda x: scores[x]["score"])
        best_score = scores[best_intent]["score"]
        
        # Convert score to confidence
        confidence = min(0.85, best_score / 10.0)  # Cap at 0.85 for keyword-based
        
        # Context boost
        if last_intent and last_intent == best_intent:
            confidence += 0.05
            confidence = min(0.9, confidence)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "reasoning": f"Keyword match: {', '.join(scores[best_intent]['matches'][:3])}"
        }
    
    def _build_keyword_classifier(self) -> Dict[str, Dict[str, float]]:
        """Build keyword-based classifier weights"""
        return {
            "emotional": {
                "feel": 3.0, "feeling": 3.0, "emotion": 3.0,
                "sad": 2.5, "happy": 2.5, "angry": 2.5, "depressed": 3.0,
                "anxious": 3.0, "worried": 2.5, "scared": 2.5,
                "love": 2.0, "hate": 2.0, "heart": 1.5,
                "relationship": 2.5, "friend": 1.5, "family": 1.5,
                "support": 2.0, "help": 1.0, "advice": 1.5,
                "lonely": 3.0, "frustrated": 2.5, "confused": 2.0
            },
            
            "technical": {
                "code": 3.0, "programming": 3.0, "python": 2.5,
                "javascript": 2.5, "java": 2.0, "html": 2.0, "css": 2.0,
                "function": 2.5, "class": 2.0, "method": 2.0,
                "algorithm": 3.0, "database": 2.5, "api": 2.5,
                "debug": 3.0, "error": 2.0, "exception": 2.5,
                "import": 2.0, "variable": 2.0, "loop": 2.0,
                "framework": 2.5, "library": 2.0, "git": 2.0,
                "compile": 2.5, "syntax": 2.5
            },
            
            "recipes": {
                "recipe": 3.0, "cook": 3.0, "cooking": 3.0,
                "bake": 3.0, "baking": 3.0, "kitchen": 2.0,
                "ingredients": 3.0, "flour": 2.0, "sugar": 2.0,
                "oven": 2.5, "temperature": 2.0, "degrees": 1.5,
                "minutes": 1.5, "tablespoon": 2.0, "teaspoon": 2.0,
                "cup": 1.5, "dish": 1.5, "meal": 2.0,
                "breakfast": 1.5, "lunch": 1.5, "dinner": 1.5,
                "food": 1.0, "eat": 1.0
            },
            
            "finance": {
                "money": 2.5, "investment": 3.0, "invest": 3.0,
                "stock": 3.0, "stocks": 3.0, "trading": 3.0,
                "portfolio": 3.0, "budget": 3.0, "savings": 2.5,
                "bank": 2.0, "loan": 2.5, "credit": 2.0,
                "debt": 2.5, "mortgage": 2.5, "insurance": 2.0,
                "tax": 2.0, "retirement": 2.5, "401k": 3.0,
                "dividend": 3.0, "interest": 2.0, "bond": 2.5,
                "cryptocurrency": 3.0, "bitcoin": 2.5,
                "dollar": 1.5, "dollars": 1.5, "price": 1.0
            },
            
            "mm_image": {
                "image": 3.0, "picture": 3.0, "photo": 3.0,
                "visual": 2.5, "see": 1.5, "look": 1.0,
                "show": 1.5, "display": 2.0, "screenshot": 3.0,
                "drawing": 2.5, "diagram": 2.5, "chart": 2.0,
                "illustration": 2.5, "color": 1.5, "pixel": 2.0
            },
            
            "mm_audio": {
                "audio": 3.0, "sound": 2.5, "music": 2.5,
                "song": 2.5, "voice": 2.5, "speech": 2.5,
                "listen": 2.0, "hear": 2.0, "recording": 3.0,
                "microphone": 2.5, "speaker": 2.0, "volume": 2.0,
                "frequency": 2.5, "pitch": 2.0, "rhythm": 2.0
            },
            
            "general": {
                "what": 0.5, "how": 0.5, "why": 0.5, "when": 0.5,
                "where": 0.5, "question": 1.0, "help": 0.5,
                "explain": 1.0, "tell": 0.5, "information": 1.0
            }
        }
