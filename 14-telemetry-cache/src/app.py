"""
Telemetry Cache Service - Structured Logging, Metrics, and Caching
Provides high-performance telemetry with Loki/Prometheus integration
"""

import json
import re
import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import redis.asyncio as redis  # type: ignore
import structlog  # type: ignore
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from prometheus_client import (  # type: ignore
    Histogram, Counter, Gauge, generate_latest
)
import aiohttp  # type: ignore


# Configure structured logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO
)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Telemetry Cache Service",
    description="Structured logging, metrics, and caching for OpenWebUI Suite",
    version="1.0.0"
)


@app.get("/healthz")
async def healthz():
    """Kubernetes style healthz alias"""
    return {"ok": True, "service": "telemetry-cache"}

# Pydantic models
class LogEvent(BaseModel):
    event: str
    payload: Dict[str, Any]


class CacheSetRequest(BaseModel):
    key: str
    data: Dict[str, Any]
    ttl: int = 3600


class LogResponse(BaseModel):
    status: str
    event_id: str
    redacted_fields: List[str]


class CacheGetResponse(BaseModel):
    hit: bool
    data: Optional[Dict[str, Any]] = None
    ttl_remaining: Optional[int] = None


class CacheSetResponse(BaseModel):
    status: str
    key: str
    expires_at: str


# PII Detection Patterns
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
    "credit_card": r'\b\d{4}[-]?\d{4}[-]?\d{4}[-]?\d{4}\b',
    "api_key": r'\b[A-Za-z0-9]{32,}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    "user_id": r'\buser[_-]?[a-z0-9]+\b',
    "session_id": r'\bsess[a-z0-9]+\b'
}

# Prometheus Metrics
TTFB_HISTOGRAM = Histogram(
    'telemetry_cache_ttfb_seconds',
    'Time to first byte',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, float('inf')]
)

TOKENS_PER_SECOND = Gauge(
    'telemetry_cache_tokens_per_second',
    'Tokens per second'
)

REPAIR_COUNTER = Counter(
    'telemetry_cache_repair_rate_total',
    'Total content repairs'
)

DRIFT_COUNTER = Counter(
    'telemetry_cache_drift_incidents_total',
    'Total drift incidents'
)

CACHE_HIT_RATE = Gauge(
    'telemetry_cache_cache_hit_rate',
    'Cache hit rate'
)

CACHE_HITS = Counter('telemetry_cache_cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('telemetry_cache_cache_misses_total', 'Total cache misses')

LOG_EVENTS = Counter('telemetry_cache_log_events_total', 'Total log events processed')


class TelemetryProcessor:
    """Handles telemetry processing with PII redaction and metrics"""

    def __init__(self, loki_url: Optional[str] = None):
        self.loki_url = loki_url
        self.session = None

    async def __aenter__(self):
        if self.loki_url:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def redact_pii(self, data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
        """Redact PII from data and return redacted fields"""
        redacted = json.loads(json.dumps(data))  # Deep copy
        redacted_fields = []

        def _redact(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        for pii_type, pattern in PII_PATTERNS.items():
                            if re.search(pattern, value, re.IGNORECASE):
                                obj[key] = f"[REDACTED_{pii_type.upper()}]"
                                if key not in redacted_fields:
                                    redacted_fields.append(key)
                                break
                    else:
                        _redact(value)
            elif isinstance(obj, list):
                for item in obj:
                    _redact(item)

        _redact(redacted)
        return redacted, redacted_fields

    async def ship_to_loki(self, event: Dict[str, Any]):
        """Ship log event to Loki"""
        if not self.session or not self.loki_url:
            return

        try:
            loki_payload = {
                "streams": [{
                    "stream": {
                        "service": "telemetry-cache",
                        "event_type": event.get("event", "unknown")
                    },
                    "values": [[
                        str(int(time.time() * 1e9)),
                        json.dumps(event)
                    ]]
                }]
            }

            async with self.session.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=loki_payload
            ) as response:
                if response.status != 204:
                    logger.warning("Failed to ship to Loki", status=response.status)

        except Exception as e:
            logger.error("Error shipping to Loki", error=str(e))

    def emit_metrics(self, event: Dict[str, Any]):
        """Emit Prometheus metrics from event"""
        payload = event.get("payload", {})

        # TTFB metric
        if "latency_ms" in payload:
            TTFB_HISTOGRAM.observe(payload["latency_ms"] / 1000.0)

        # Tokens per second
        if "tokens" in payload and "latency_ms" in payload:
            latency_seconds = payload["latency_ms"] / 1000.0
            if latency_seconds > 0:
                tokens_per_second = payload["tokens"] / latency_seconds
                TOKENS_PER_SECOND.set(tokens_per_second)

        # Repair rate
        if event.get("event") == "content_repair":
            REPAIR_COUNTER.inc()

        # Drift incidents
        if event.get("event") == "policy_drift":
            DRIFT_COUNTER.inc()


class CacheManager:
    """Redis-based cache manager with TTL support"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data"""
        if not self.redis:
            return None

        try:
            data = await self.redis.get(key)
            if data:
                CACHE_HITS.inc()
                # Get TTL
                ttl = await self.redis.ttl(key)
                cached_data = json.loads(data)
                return {"data": cached_data, "ttl": ttl}
            else:
                CACHE_MISSES.inc()
                return None
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None

    async def set(self, key: str, data: Dict[str, Any], ttl: int = 3600):
        """Set cached data with TTL"""
        if not self.redis:
            return

        try:
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.info("Cache set", key=key, ttl=ttl)
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))

    async def delete(self, key: str):
        """Delete cached data"""
        if not self.redis:
            return

        try:
            await self.redis.delete(key)
            logger.info("Cache delete", key=key)
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))

    async def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if not self.redis:
            return 0.0

        try:
            hits = float(await self.redis.get('cache_hits') or 0)
            misses = float(await self.redis.get('cache_misses') or 0)
            total = hits + misses
            hit_rate = hits / total if total > 0 else 0.0
            CACHE_HIT_RATE.set(hit_rate)
            return hit_rate
        except Exception as e:
            logger.error("Error calculating hit rate", error=str(e))
            return 0.0


def normalize_tool_args(tool: str, args: Dict[str, Any]) -> str:
    """Normalize tool arguments into cache key"""
    # Sort keys for consistency
    sorted_args = sorted(args.items())

    # Normalize values
    normalized = []
    for key, value in sorted_args:
        if isinstance(value, float):
            # Round floats to 2 decimal places
            normalized_value = f"{value:.2f}"
        elif isinstance(value, str):
            # Lowercase and remove special chars
            normalized_value = re.sub(r'[^a-z0-9]', '_', value.lower())[:50]
        else:
            normalized_value = str(value)

        normalized.append(f"{key}:{normalized_value}")

    return f"tool:{tool}:{':'.join(normalized)}"


# Global instances
telemetry_processor = TelemetryProcessor()
cache_manager = CacheManager()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global telemetry_processor, cache_manager

    # Initialize telemetry processor
    loki_url = "http://localhost:3100"  # Configure as needed
    telemetry_processor = TelemetryProcessor(loki_url=loki_url)
    await telemetry_processor.__aenter__()

    # Initialize cache manager
    redis_url = "redis://localhost:6379"  # Configure as needed
    cache_manager = CacheManager(redis_url=redis_url)
    await cache_manager.initialize()

    logger.info("Telemetry Cache Service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await telemetry_processor.__aexit__(None, None, None)
    await cache_manager.close()


@app.post("/log", response_model=LogResponse)
async def log_event(event: LogEvent):
    """Log structured event with PII redaction"""
    try:
        start_time = time.time()

        # Generate event ID
        event_id = str(uuid.uuid4())

        # Add timestamp if not present
        if "timestamp" not in event.payload:
            event.payload["timestamp"] = datetime.utcnow().isoformat()

        # Redact PII
        redacted_payload, redacted_fields = (
            telemetry_processor.redact_pii(event.payload)
        )

        # Emit metrics
        telemetry_processor.emit_metrics(event.dict())

        # Ship to Loki (async)
        # Note: In production, this should be queued for async processing
        # await telemetry_processor.ship_to_loki(redacted_event)

        # Log locally
        logger.info(
            "Event logged",
            event_id=event_id,
            event_type=event.event,
            redacted_fields=redacted_fields,
            processing_time=time.time() - start_time
        )

        LOG_EVENTS.inc()

        return LogResponse(
            status="logged",
            event_id=event_id,
            redacted_fields=redacted_fields
        )

    except Exception as e:
        logger.error("Error logging event", error=str(e))
        raise HTTPException(status_code=500, detail="Logging failed")


@app.get("/cache/get")
async def get_cache(key: str = Query(..., description="Cache key")):
    """Retrieve cached data"""
    try:
        result = await cache_manager.get(key)

        if result:
            return CacheGetResponse(
                hit=True,
                data=result["data"],
                ttl_remaining=result["ttl"]
            )
        else:
            return CacheGetResponse(hit=False)

    except Exception as e:
        logger.error("Error getting cache", key=key, error=str(e))
        raise HTTPException(status_code=500, detail="Cache retrieval failed")


@app.post("/cache/set", response_model=CacheSetResponse)
async def set_cache(request: CacheSetRequest):
    """Store data in cache with TTL"""
    try:
        await cache_manager.set(request.key, request.data, request.ttl)

        expires_at = datetime.utcnow() + timedelta(seconds=request.ttl)

        return CacheSetResponse(
            status="cached",
            key=request.key,
            expires_at=expires_at.isoformat()
        )

    except Exception as e:
        logger.error("Error setting cache", key=request.key, error=str(e))
        raise HTTPException(status_code=500, detail="Cache storage failed")


@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        # Update cache hit rate
        await cache_manager.get_hit_rate()

        return generate_latest()

    except Exception as e:
        logger.error("Error generating metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Metrics generation failed"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_ok = False
        try:
            if cache_manager.redis:
                await cache_manager.redis.ping()
                redis_ok = True
        except Exception:
            pass

        return {
            "status": "healthy" if redis_ok else "degraded",
            "version": "1.0.0",
            "redis_connected": redis_ok,
            "loki_configured": telemetry_processor.loki_url is not None
        }

    except Exception as e:
        logger.error("Health check error", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        hit_rate = await cache_manager.get_hit_rate()

        return {
            "hit_rate": hit_rate,
            "total_hits": CACHE_HITS._value,
            "total_misses": CACHE_MISSES._value,
            "total_requests": CACHE_HITS._value + CACHE_MISSES._value
        }

    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="Stats retrieval failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8114)
