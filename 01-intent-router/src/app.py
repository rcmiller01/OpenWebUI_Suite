"""
Intent Router FastAPI Application

Fast CPU-based classifier to route user inputs to appropriate processing lanes.
Optimized for <50ms response time with <100MB footprint.
"""

import time
import logging
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .classifier import IntentClassifier
from .rules import RuleEngine, build_route

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Intent Router",
    description="Fast intent classification service for OpenWebUI Suite",
    version="1.0.0"
)

# Global components
classifier: Optional[IntentClassifier] = None
rule_engine: Optional[RuleEngine] = None


class AttachmentInfo(BaseModel):
    """Attachment metadata"""
    type: str = Field(
        ..., description="Attachment type (image, audio, document, etc.)"
    )
    size: Optional[int] = Field(
        None, description="File size in bytes"
    )
    mime_type: Optional[str] = Field(
        None, description="MIME type"
    )
    filename: Optional[str] = Field(
        None, description="Original filename"
    )


class ClassificationRequest(BaseModel):
    """Request model for intent classification"""
    text: str = Field(
        ..., description="Input text to classify", max_length=10000
    )
    last_intent: Optional[str] = Field(
        None, description="Previously detected intent for context"
    )
    attachments: Optional[List[AttachmentInfo]] = Field(
        None, description="Attached files/media"
    )


class ClassificationResponse(BaseModel):
    """Response model for intent classification"""
    intent: str = Field(
        ..., description="Detected intent category"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score"
    )
    needs_remote: bool = Field(
        ..., description="Whether remote processing is recommended"
    )
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )
    reasoning: Optional[str] = Field(
        None, description="Classification reasoning (debug)"
    )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    components: Dict[str, bool]
    version: str


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global classifier, rule_engine
    
    logger.info("Starting Intent Router service...")
    
    try:
        # Initialize rule engine
        rule_engine = RuleEngine()
        logger.info("Rule engine initialized")
        
    # Initialize ML classifier
        classifier = IntentClassifier()
        await classifier.load_model()
        logger.info("Intent classifier initialized")
        
        logger.info("Intent Router started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        components={
            "rule_engine": rule_engine is not None,
            "classifier": classifier is not None
        },
        version="1.0.0"
    )


@app.get("/healthz")
async def healthz():
    return {"ok": True, "components": {
        "rule_engine": bool(rule_engine),
        "classifier": bool(classifier)
    }}


@app.post("/classify", response_model=ClassificationResponse)
async def classify_intent(request: ClassificationRequest):
    """
    Classify user input intent and determine remote processing needs
    
    Returns intent category, confidence score, and remote processing
    recommendation.
    """
    start_time = time.time()
    
    try:
        # Input validation
        if not request.text.strip():
            raise HTTPException(
                status_code=400, detail="Text input cannot be empty"
            )
        
        # Step 1: Rule-based pre-filtering for obvious cases
        assert rule_engine is not None  # runtime invariant after startup
        rule_result = rule_engine.classify(
            text=request.text,
            context={"attachments": request.attachments, "last_intent": request.last_intent}
        )
        
        if rule_result["confident"]:
            # Rule engine is confident, use its result
            processing_time = (time.time() - start_time) * 1000
            
            return ClassificationResponse(
                intent=rule_result["intent"],
                confidence=rule_result["confidence"],
                needs_remote=rule_result["needs_remote"],
                processing_time_ms=processing_time,
                reasoning=f"Rule-based: {rule_result['reasoning']}"
            )
        
        # Step 2: ML classifier for ambiguous cases
        assert classifier is not None  # runtime invariant after startup
        ml_result = await classifier.classify(
            text=request.text,
            attachments=request.attachments,
            last_intent=request.last_intent,
        )
        
        # Step 3: Combine rule and ML results
        final_intent = ml_result["intent"]
        final_confidence = ml_result["confidence"]
        
        # Override with rule result if rule has higher confidence
        if rule_result["confidence"] > ml_result["confidence"]:
            final_intent = rule_result["intent"]
            final_confidence = rule_result["confidence"]
        
        # Step 4: Determine remote processing needs
        needs_remote = _should_use_remote(
            text=request.text,
            intent=final_intent,
            confidence=final_confidence,
            attachments=request.attachments
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ClassificationResponse(
            intent=final_intent,
            confidence=final_confidence,
            needs_remote=needs_remote,
            processing_time_ms=processing_time,
            reasoning=(
                f"ML + Rules: "
                f"{ml_result.get('reasoning', 'Combined classification')}"
            ),
        )
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Classification failed: {str(e)}"
        )


def _should_use_remote(
    text: str,
    intent: str,
    confidence: float,
    attachments: Optional[List[AttachmentInfo]] = None,
) -> bool:
    """
    Determine if remote processing is needed based on multiple factors
    """
    # Long text requires remote processing
    if len(text) > 1000:
        return True
    
    # Low confidence suggests complex reasoning needed
    if confidence < 0.8:
        return True
    
    # Multi-modal content requires remote processing
    if attachments:
        for attachment in attachments:
            if attachment.type in ["image", "audio", "video", "document"]:
                return True
    
    # Certain intents typically need more powerful processing
    remote_intents = {"technical", "mm_image", "mm_audio", "finance"}
    if intent in remote_intents:
        return True
    
    # Complex patterns that suggest deep reasoning needed
    complex_patterns = [
        "explain", "analyze", "compare", "summarize", "create", "generate",
        "write", "compose", "design", "plan", "strategy", "algorithm"
    ]
    
    text_lower = text.lower()
    complex_count = sum(
        1 for pattern in complex_patterns if pattern in text_lower
    )
    if complex_count >= 2:
        return True
    
    return False


class RouteRequest(BaseModel):
    """Request model for routing"""
    user_text: str = Field(..., description="User input text to route", max_length=10000)
    tags: Optional[List[str]] = Field(default=None, description="Optional tags to consider")


class RouteResponse(BaseModel):
    """Response model for routing"""
    family: str = Field(..., description="Content family classification")
    emotion_template_id: str = Field(..., description="Emotion template to apply")
    provider: str = Field(..., description="Recommended provider (local/openrouter)")
    openrouter_model_priority: List[str] = Field(..., description="Prioritized model list for OpenRouter")
    tags: List[str] = Field(..., description="Applied tags")


@app.post("/route", response_model=RouteResponse)
async def route(request: RouteRequest):
    """Route user input based on content family and return processing recommendations"""
    try:
        # Use the new family-based routing
        route_info = build_route(request.user_text, request.tags)
        
        return RouteResponse(
            family=route_info["family"],
            emotion_template_id=route_info["emotion_template_id"],
            provider=route_info["provider"],
            openrouter_model_priority=route_info["openrouter_model_priority"],
            tags=route_info["tags"]
        )
    
    except Exception as e:
        logger.error(f"Error in routing: {e}")
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Intent Router",
        "version": "1.0.0",
        "description": "Fast intent classification for OpenWebUI Suite",
        "endpoints": {
            "classify": "/classify",
            "route": "/route",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8101)
