#!/usr/bin/env python3
"""
Feeling Engine service for the OpenWebUI Suite

Provides affect tagging, tone policy, and micro-critic functionality.
Fast CPU inference with <50ms latency per call.

Features:
- Sentiment analysis (positive/negative/neutral)
- Emotion detection (joy, sadness, anger, fear, surprise, disgust)
- Dialog act classification
- Urgency detection
- Tone policy generation
- Text critique and cleaning
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import re
import time
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load emotion templates
TEMPLATES_PATH = os.getenv("EMOTION_TEMPLATES_PATH", "/app/emotion_templates.json")
try:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        EMOTION_TEMPLATES: Dict[str, Dict] = {t["id"]: t for t in json.load(f)}
    logger.info(f"Loaded {len(EMOTION_TEMPLATES)} emotion templates")
except FileNotFoundError:
    logger.warning(f"Emotion templates file not found at {TEMPLATES_PATH}")
    EMOTION_TEMPLATES: Dict[str, Dict] = {"none": {"id": "none", "label": "No emotional augmentation", "system_suffix": ""}}
except Exception as e:
    logger.error(f"Error loading emotion templates: {e}")
    EMOTION_TEMPLATES: Dict[str, Dict] = {"none": {"id": "none", "label": "No emotional augmentation", "system_suffix": ""}}

app = FastAPI(
    title="Feeling Engine",
    description="Affect tagging, tone policy, and micro-critic service",
    version="1.0.0"
)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "feeling-engine"}

# Models
class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Text to analyze", max_length=10000)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class ToneRequest(BaseModel):
    text: str = Field(..., description="Text to generate tone policy for", max_length=10000)
    target_audience: Optional[str] = Field(default="general", description="Target audience")

class CritiqueRequest(BaseModel):
    text: str = Field(..., description="Text to critique and clean", max_length=10000)
    max_tokens: int = Field(default=100, description="Maximum tokens to keep")


class AugmentRequest(BaseModel):
    system_prompt: str = Field(..., description="System prompt to augment", max_length=50000)
    emotion_template_id: Optional[str] = Field(default="none", description="Emotion template ID to apply")


class AnalyzeResponse(BaseModel):
    sentiment: str = Field(..., description="Overall sentiment: positive/negative/neutral")
    emotions: List[str] = Field(default=[], description="Detected emotions")
    dialog_act: str = Field(..., description="Dialog act classification")
    urgency: str = Field(..., description="Urgency level: low/medium/high")
    confidence: float = Field(..., description="Analysis confidence 0-1")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class ToneResponse(BaseModel):
    tone_policies: List[str] = Field(..., description="Recommended tone policies")
    primary_tone: str = Field(..., description="Primary recommended tone")
    confidence: float = Field(..., description="Tone analysis confidence 0-1")

class CritiqueResponse(BaseModel):
    cleaned_text: str = Field(..., description="Critiqued and cleaned text")
    original_tokens: int = Field(..., description="Original text token count")
    cleaned_tokens: int = Field(..., description="Cleaned text token count")
    changes_made: List[str] = Field(default=[], description="Description of changes")


class AugmentResponse(BaseModel):
    system_prompt: str = Field(..., description="Augmented system prompt")
    template_id: str = Field(..., description="Applied template ID")
    template_label: str = Field(..., description="Applied template label")


# Utility functions
def apply_emotion_suffix(system_prompt: str, template_id: Optional[str]) -> Dict[str, str]:
    """Apply emotion template suffix to system prompt"""
    tpl = EMOTION_TEMPLATES.get(template_id or "none", EMOTION_TEMPLATES["none"])
    suffix = (tpl.get("system_suffix") or "").strip()
    augmented_prompt = system_prompt if not suffix else f"{system_prompt.rstrip()}\n\n{suffix}"
    
    return {
        "system_prompt": augmented_prompt,
        "template_id": tpl["id"],
        "template_label": tpl.get("label", "Unknown template")
    }


# Rule-based models for fast inference
class SentimentAnalyzer:
    """Simple rule-based sentiment analyzer"""

    def __init__(self):
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'happy', 'joy', 'pleased', 'satisfied', 'awesome',
            'perfect', 'brilliant', 'outstanding', 'superb', 'terrific'
        }

        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'sad',
            'angry', 'frustrated', 'annoyed', 'disappointed', 'upset', 'worried',
            'scared', 'afraid', 'terrible', 'dreadful', 'pathetic', 'useless'
        }

        self.intensifiers = {'very', 'really', 'extremely', 'so', 'too', 'quite'}

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        positive_score = 0
        negative_score = 0

        for i, word in enumerate(words):
            if word in self.positive_words:
                # Check for intensifier before
                multiplier = 1.5 if i > 0 and words[i-1] in self.intensifiers else 1.0
                positive_score += 1 * multiplier
            elif word in self.negative_words:
                multiplier = 1.5 if i > 0 and words[i-1] in self.intensifiers else 1.0
                negative_score += 1 * multiplier

        total_words = len(words)
        if total_words == 0:
            return {"sentiment": "neutral", "confidence": 0.5}

        # Calculate sentiment
        if positive_score > negative_score:
            sentiment = "positive"
            confidence = min(0.9, positive_score / max(1, total_words * 0.1))
        elif negative_score > positive_score:
            sentiment = "negative"
            confidence = min(0.9, negative_score / max(1, total_words * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.5

        return {"sentiment": sentiment, "confidence": confidence}

class EmotionDetector:
    """Simple rule-based emotion detector"""

    def __init__(self):
        self.emotion_patterns = {
            'joy': ['happy', 'excited', 'delighted', 'thrilled', 'joyful', 'cheerful', 'glad'],
            'sadness': ['sad', 'unhappy', 'depressed', 'sorrow', 'grief', 'melancholy', 'blue'],
            'anger': ['angry', 'mad', 'furious', 'irritated', 'annoyed', 'frustrated', 'rage'],
            'fear': ['scared', 'afraid', 'terrified', 'anxious', 'worried', 'frightened', 'panic'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'startled', 'unexpected'],
            'disgust': ['disgusted', 'repulsed', 'gross', 'sick', 'nauseous', 'revolted']
        }

    def detect(self, text: str) -> List[str]:
        """Detect emotions in text"""
        text_lower = text.lower()
        detected_emotions = []

        for emotion, patterns in self.emotion_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    detected_emotions.append(emotion)
                    break  # Only add each emotion once

        return detected_emotions

class DialogActClassifier:
    """Simple rule-based dialog act classifier"""

    def __init__(self):
        self.act_patterns = {
            'question': [r'\?$', r'what', r'how', r'why', r'when', r'where', r'who', r'which'],
            'statement': [r'\.$', r'is', r'are', r'was', r'were', r'has', r'have'],
            'command': [r'^please', r'can you', r'would you', r'could you', r'do this', r'make'],
            'exclamation': [r'!$', r'wow', r'oh', r'ah', r'yeah', r'yes'],
            'acknowledgment': [r'i see', r'okay', r'alright', r'got it', r'understood', r'agreed']
        }

    def classify(self, text: str) -> str:
        """Classify dialog act"""
        text_lower = text.lower().strip()

        # Check patterns in order of specificity
        for act, patterns in self.act_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return act

        # Default to statement if no pattern matches
        return 'statement'

class UrgencyDetector:
    """Simple rule-based urgency detector"""

    def __init__(self):
        self.urgent_words = {
            'urgent', 'emergency', 'asap', 'immediately', 'right now', 'quickly',
            'critical', 'important', 'deadline', 'rush', 'hurry', 'fast'
        }

        self.low_urgency_words = {
            'whenever', 'sometime', 'eventually', 'later', 'no rush', 'take your time'
        }

    def detect(self, text: str) -> str:
        """Detect urgency level"""
        text_lower = text.lower()

        urgent_count = sum(1 for word in self.urgent_words if word in text_lower)
        low_count = sum(1 for word in self.low_urgency_words if word in text_lower)

        if urgent_count > 0:
            return 'high'
        elif low_count > 0:
            return 'low'
        else:
            return 'medium'

class TonePolicyGenerator:
    """Generate tone policies based on content analysis"""

    def __init__(self):
        self.formal_indicators = ['professional', 'formal', 'business', 'corporate', 'academic']
        self.casual_indicators = ['casual', 'friendly', 'relaxed', 'informal', 'chatty']
        self.emotional_indicators = ['emotional', 'passionate', 'excited', 'enthusiastic']

    def generate_policies(self, text: str, target_audience: str = "general") -> Dict[str, Any]:
        """Generate tone policies for the given text"""
        text_lower = text.lower()

        policies = []
        primary_tone = "neutral"

        # Analyze formality
        formal_score = sum(1 for word in self.formal_indicators if word in text_lower)
        casual_score = sum(1 for word in self.casual_indicators if word in text_lower)

        if formal_score > casual_score:
            policies.append("Use formal language and professional tone")
            primary_tone = "formal"
        elif casual_score > formal_score:
            policies.append("Use casual, friendly language")
            primary_tone = "casual"

        # Analyze emotional content
        emotional_score = sum(1 for word in self.emotional_indicators if word in text_lower)
        if emotional_score > 0:
            policies.append("Maintain enthusiastic and engaging tone")
            if primary_tone == "neutral":
                primary_tone = "enthusiastic"

        # Audience-specific policies
        if target_audience == "technical":
            policies.append("Use technical terminology appropriately")
            policies.append("Focus on clarity and precision")
        elif target_audience == "general":
            policies.append("Use accessible language for broad audience")
        elif target_audience == "expert":
            policies.append("Use domain-specific terminology")
            policies.append("Assume background knowledge")

        # Default policies
        if not policies:
            policies = [
                "Use clear and concise language",
                "Maintain professional yet approachable tone",
                "Be helpful and informative"
            ]

        return {
            "tone_policies": policies,
            "primary_tone": primary_tone,
            "confidence": 0.8
        }

class TextCritic:
    """Text critique and cleaning functionality"""

    def __init__(self):
        self.filler_words = {'um', 'uh', 'like', 'you know', 'sort of', 'kind of', 'basically', 'actually'}
        self.repetitive_patterns = [
            r'\b(\w+)\s+\1\b',  # Word repetition
            r'(\w{3,})\s+(\w{3,})\s+\1\s+\2',  # Phrase repetition
        ]

    def critique(self, text: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Critique and clean text"""
        original_text = text
        changes = []

        # Remove excessive filler words
        cleaned_text = text
        filler_count = 0
        for filler in self.filler_words:
            pattern = r'\b' + re.escape(filler) + r'\b'
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            if len(matches) > 2:  # Remove if more than 2 occurrences
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
                filler_count += len(matches)
                changes.append(f"Removed {len(matches)} instances of filler word '{filler}'")

        # Remove repetitive phrases
        for pattern in self.repetitive_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        phrase = ' '.join(match)
                    else:
                        phrase = match
                    # Only remove if phrase appears more than once
                    if cleaned_text.count(phrase) > 1:
                        cleaned_text = re.sub(re.escape(phrase), '', cleaned_text, count=1)
                        changes.append(f"Removed repetitive phrase '{phrase}'")

        # Remove excessive whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Truncate if too long (rough token estimation)
        original_tokens = len(original_text.split())
        cleaned_tokens = len(cleaned_text.split())

        if cleaned_tokens > max_tokens:
            words = cleaned_text.split()
            cleaned_text = ' '.join(words[:max_tokens])
            changes.append(f"Truncated text to {max_tokens} tokens")
            cleaned_tokens = max_tokens

        # Remove trailing punctuation issues
        cleaned_text = re.sub(r'[.!?]+$', '.', cleaned_text)

        return {
            "cleaned_text": cleaned_text,
            "original_tokens": original_tokens,
            "cleaned_tokens": cleaned_tokens,
            "changes_made": changes
        }

# Initialize models
sentiment_analyzer = SentimentAnalyzer()
emotion_detector = EmotionDetector()
dialog_act_classifier = DialogActClassifier()
urgency_detector = UrgencyDetector()
tone_policy_generator = TonePolicyGenerator()
text_critic = TextCritic()

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Feeling Engine",
        "version": "1.0.0",
        "description": "Affect tagging, tone policy, and micro-critic service",
        "endpoints": {
            "analyze": "/affect/analyze",
            "tone": "/affect/tone",
            "critique": "/affect/critique",
            "health": "/health"
        },
        "features": [
            "Sentiment analysis",
            "Emotion detection",
            "Dialog act classification",
            "Urgency detection",
            "Tone policy generation",
            "Text critique and cleaning"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "models_loaded": True
    }

@app.post("/affect/analyze", response_model=AnalyzeResponse)
async def analyze_affect(request: AnalyzeRequest):
    """Analyze affect: sentiment, emotions, dialog act, urgency"""
    start_time = time.time()

    try:
        # Run all analyses
        sentiment_result = sentiment_analyzer.analyze(request.text)
        emotions = emotion_detector.detect(request.text)
        dialog_act = dialog_act_classifier.classify(request.text)
        urgency = urgency_detector.detect(request.text)

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return AnalyzeResponse(
            sentiment=sentiment_result["sentiment"],
            emotions=emotions,
            dialog_act=dialog_act,
            urgency=urgency,
            confidence=sentiment_result["confidence"],
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Error in affect analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/affect/tone", response_model=ToneResponse)
async def generate_tone_policy(request: ToneRequest):
    """Generate tone policies for the given text"""
    try:
        result = tone_policy_generator.generate_policies(
            request.text,
            request.target_audience or "general"
        )

        return ToneResponse(
            tone_policies=result["tone_policies"],
            primary_tone=result["primary_tone"],
            confidence=result["confidence"]
        )

    except Exception as e:
        logger.error(f"Error generating tone policy: {e}")
        raise HTTPException(status_code=500, detail=f"Tone policy generation failed: {str(e)}")

@app.post("/affect/critique", response_model=CritiqueResponse)
async def critique_text(request: CritiqueRequest):
    """Critique and clean text"""
    try:
        result = text_critic.critique(request.text, request.max_tokens)

        return CritiqueResponse(
            cleaned_text=result["cleaned_text"],
            original_tokens=result["original_tokens"],
            cleaned_tokens=result["cleaned_tokens"],
            changes_made=result["changes_made"]
        )

    except Exception as e:
        logger.error(f"Error critiquing text: {e}")
        raise HTTPException(status_code=500, detail=f"Text critique failed: {str(e)}")


@app.post("/augment", response_model=AugmentResponse)
async def augment_system_prompt(request: AugmentRequest):
    """Apply emotion template to augment system prompt"""
    try:
        result = apply_emotion_suffix(request.system_prompt, request.emotion_template_id)
        
        return AugmentResponse(
            system_prompt=result["system_prompt"],
            template_id=result["template_id"],
            template_label=result["template_label"]
        )
    
    except Exception as e:
        logger.error(f"Error augmenting system prompt: {e}")
        raise HTTPException(status_code=500, detail=f"System prompt augmentation failed: {str(e)}")


@app.get("/templates")
async def get_emotion_templates():
    """Get available emotion templates"""
    return {
        "templates": list(EMOTION_TEMPLATES.values()),
        "count": len(EMOTION_TEMPLATES)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8103)
