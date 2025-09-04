# 14-Telemetry-Cache Agent

## Overview

The Telemetry Cache service provides structured logging, metrics collection, and response caching for the OpenWebUI Suite. It implements high-performance telemetry with Loki/Prometheus integration, Redis-based caching with normalized keys, and comprehensive KPI tracking without exposing PII.

## Architecture

- **Structured Logging**: JSON-formatted logs with PII redaction
- **Metrics Collection**: Prometheus-compatible metrics with histogram buckets
- **Response Caching**: Redis-based cache with normalized tool argument keys
- **High Performance**: Async processing for high-QPS logging
- **PII Protection**: Automatic secret redaction and sanitization
- **KPI Tracking**: Real-time metrics for TTFB, throughput, and cache performance

## Core Components

### Telemetry Engine

- **Log Aggregation**: Structured JSON logging with metadata
- **Metrics Emission**: Prometheus histogram and counter metrics
- **PII Redaction**: Automatic detection and masking of sensitive data
- **Async Processing**: Non-blocking log processing for high throughput

### Cache System

- **Redis Backend**: High-performance key-value storage
- **Key Normalization**: Consistent key generation from tool arguments
- **TTL Management**: Configurable cache expiration
- **Hit Rate Tracking**: Cache performance metrics

### Metrics Pipeline

- **Prometheus Integration**: Standard metrics format
- **Loki Integration**: Structured log shipping
- **KPI Calculation**: Real-time performance indicators
- **Alert Generation**: Threshold-based alerting

## API Endpoints

### POST /log

Log structured events with automatic PII redaction.

**Request:**

```json
{
  "event": "tool_execution|response_generation|policy_violation",
  "payload": {
    "timestamp": "2025-09-03T10:30:00Z",
    "service": "pipelines-gateway",
    "tool": "generate_response",
    "args": {
      "model": "llama2",
      "prompt": "Hello world",
      "temperature": 0.7
    },
    "response": {
      "text": "Hello! How can I help you?",
      "tokens": 150,
      "latency_ms": 250
    },
    "metadata": {
      "user_id": "user123",
      "session_id": "sess456",
      "request_id": "req789"
    }
  }
}
```

**Response:**

```json
{
  "status": "logged",
  "event_id": "evt_1234567890",
  "redacted_fields": ["user_id", "session_id"]
}
```

### GET /cache/get

Retrieve cached response by normalized key.

**Request:**

```http
GET /cache/get?key=tool:generate_response:model:llama2:temp:0.7:prompt:hello_world
```

**Response:**

```json
{
  "hit": true,
  "data": {
    "response": "Hello! How can I help you?",
    "timestamp": "2025-09-03T10:30:00Z",
    "ttl_remaining": 3600
  }
}
```

### POST /cache/set

Store response in cache with TTL.

**Request:**

```json
{
  "key": "tool:generate_response:model:llama2:temp:0.7:prompt:hello_world",
  "data": {
    "response": "Hello! How can I help you?",
    "tokens": 150,
    "latency_ms": 250
  },
  "ttl": 3600
}
```

**Response:**

```json
{
  "status": "cached",
  "key": "tool:generate_response:model:llama2:temp:0.7:prompt:hello_world",
  "expires_at": "2025-09-03T11:30:00Z"
}
```

### GET /metrics

Prometheus-compatible metrics endpoint.

**Response:**

```prometheus
# HELP telemetry_cache_ttfb_seconds Time to first byte histogram
# TYPE telemetry_cache_ttfb_seconds histogram
telemetry_cache_ttfb_seconds_bucket{le="0.1"} 150
telemetry_cache_ttfb_seconds_bucket{le="0.5"} 450
telemetry_cache_ttfb_seconds_bucket{le="1.0"} 780
telemetry_cache_ttfb_seconds_bucket{le="2.0"} 920
telemetry_cache_ttfb_seconds_bucket{le="5.0"} 980
telemetry_cache_ttfb_seconds_bucket{le="+Inf"} 1000
telemetry_cache_ttfb_seconds_sum 1250.5
telemetry_cache_ttfb_seconds_count 1000

# HELP telemetry_cache_tokens_per_second Tokens per second gauge
# TYPE telemetry_cache_tokens_per_second gauge
telemetry_cache_tokens_per_second 45.2

# HELP telemetry_cache_repair_rate Repair rate counter
# TYPE telemetry_cache_repair_rate counter
telemetry_cache_repair_rate_total 23

# HELP telemetry_cache_drift_incidents Drift incident counter
# TYPE telemetry_cache_drift_incidents counter
telemetry_cache_drift_incidents_total 5

# HELP telemetry_cache_cache_hit_rate Cache hit rate gauge
# TYPE telemetry_cache_cache_hit_rate gauge
telemetry_cache_cache_hit_rate 0.85
```

## Key Normalization

### Tool Argument Normalization

```python
def normalize_tool_args(tool: str, args: dict) -> str:
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
```

### Examples

```python
# Input args
{
    "model": "Llama-2-7B",
    "temperature": 0.7,
    "prompt": "Hello World!",
    "max_tokens": 100
}

# Normalized key
"tool:generate_response:model:llama_2_7b:temperature:0.70:max_tokens:100:prompt:hello_world"
```

## PII Redaction

### Automatic Detection Patterns

```python
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
    "credit_card": r'\b\d{4}[-]?\d{4}[-]?\d{4}[-]?\d{4}\b',
    "api_key": r'\b[A-Za-z0-9]{32,}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    "user_id": r'\buser[_-]?[a-z0-9]+\b',
    "session_id": r'\bsession[_-]?[a-z0-9]+\b'
}
```

### Redaction Process

```python
def redact_pii(data: dict) -> tuple[dict, list]:
    """Redact PII from data and return redacted fields"""
    redacted = json.loads(json.dumps(data))  # Deep copy
    redacted_fields = []

    def _redact(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    for pii_type, pattern in PII_PATTERNS.items():
                        if re.search(pattern, value):
                            obj[key] = f"[REDACTED_{pii_type.upper()}]"
                            redacted_fields.append(key)
                            break
                else:
                    _redact(value)
        elif isinstance(obj, list):
            for item in obj:
                _redact(item)

    _redact(redacted)
    return redacted, redacted_fields
```

## Metrics Collection

### KPI Definitions

#### Time to First Byte (TTFB)

- **Metric**: `telemetry_cache_ttfb_seconds`
- **Type**: Histogram with buckets [0.1, 0.5, 1.0, 2.0, 5.0, +Inf]
- **Description**: Time from request start to first response byte

#### Tokens per Second

- **Metric**: `telemetry_cache_tokens_per_second`
- **Type**: Gauge
- **Description**: Average token generation rate

#### Repair Rate

- **Metric**: `telemetry_cache_repair_rate_total`
- **Type**: Counter
- **Description**: Number of content repairs performed

#### Drift Incidents

- **Metric**: `telemetry_cache_drift_incidents_total`
- **Type**: Counter
- **Description**: Number of policy drift incidents detected

#### Cache Hit Rate

- **Metric**: `telemetry_cache_cache_hit_rate`
- **Type**: Gauge
- **Description**: Ratio of cache hits to total cache requests

### Metrics Implementation

```python
from prometheus_client import Histogram, Counter, Gauge

# TTFB Histogram
TTFB_HISTOGRAM = Histogram(
    'telemetry_cache_ttfb_seconds',
    'Time to first byte',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, float('inf')]
)

# Tokens per second gauge
TOKENS_PER_SECOND = Gauge(
    'telemetry_cache_tokens_per_second',
    'Tokens per second'
)

# Repair rate counter
REPAIR_COUNTER = Counter(
    'telemetry_cache_repair_rate_total',
    'Total content repairs'
)

# Drift incidents counter
DRIFT_COUNTER = Counter(
    'telemetry_cache_drift_incidents_total',
    'Total drift incidents'
)

# Cache hit rate gauge
CACHE_HIT_RATE = Gauge(
    'telemetry_cache_cache_hit_rate',
    'Cache hit rate'
)
```

## Cache Management

### Redis Configuration

```python
import redis.asyncio as redis

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[dict]:
        """Get cached data"""
        data = await self.redis.get(key)
        if data:
            CACHE_HITS.inc()
            return json.loads(data)
        CACHE_MISSES.inc()
        return None

    async def set(self, key: str, data: dict, ttl: int = 3600):
        """Set cached data with TTL"""
        await self.redis.setex(key, ttl, json.dumps(data))

    async def delete(self, key: str):
        """Delete cached data"""
        await self.redis.delete(key)

    async def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        hits = await self.redis.get('cache_hits') or 0
        misses = await self.redis.get('cache_misses') or 0
        total = hits + misses
        return hits / total if total > 0 else 0.0
```

## Integration Patterns

### Loki Log Shipping

```yaml
# loki-config.yaml
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: telemetry-cache
    static_configs:
      - targets:
          - telemetry-cache:8114
    relabel_configs:
      - source_labels: [__address__]
        target_label: __address__
        replacement: telemetry-cache:8114
```

### Prometheus Scraping

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'telemetry-cache'
    static_configs:
      - targets: ['telemetry-cache:8114']
    metrics_path: '/metrics'
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  telemetry-cache:
    build: .
    ports:
      - "8114:8114"
    environment:
      - REDIS_URL=redis://redis:6379
      - LOKI_URL=http://loki:3100
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  redis-exporter:
    image: oliver006/redis_exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis:6379
    depends_on:
      - redis

  loki:
    image: grafana/loki:2.8.0
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

volumes:
  redis_data:
  loki_data:
  prometheus_data:
```

## Performance Optimization

### Async Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TelemetryProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.queue = asyncio.Queue()

    async def process_log(self, event: dict):
        """Async log processing"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._sync_process_log,
            event
        )

    def _sync_process_log(self, event: dict):
        """Synchronous log processing"""
        # Redact PII
        redacted, fields = redact_pii(event)

        # Emit metrics
        self._emit_metrics(event)

        # Ship to Loki
        self._ship_to_loki(redacted)
```

### Connection Pooling

```python
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

# Redis connection pool
redis_pool = ConnectionPool.from_url(
    "redis://localhost:6379",
    max_connections=20,
    decode_responses=True
)

redis_client = redis.Redis(connection_pool=redis_pool)
```

## Security Considerations

### Data Sanitization

- **Input Validation**: Strict schema validation for all inputs
- **Output Encoding**: Safe JSON serialization
- **Rate Limiting**: Request rate limiting to prevent abuse
- **Authentication**: API key authentication for sensitive endpoints

### PII Protection

- **Pattern Matching**: Comprehensive PII detection patterns
- **Hash-based Keys**: Non-reversible user identifiers
- **Data Retention**: Configurable log retention policies
- **Access Control**: Role-based access to sensitive logs

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start Loki
docker run -d -p 3100:3100 grafana/loki:2.8.0

# Start Prometheus
docker run -d -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# Run service
uvicorn src.app:app --reload --port 8114
```

### Testing Strategy

```python
def test_high_qps_logging():
    """Test high-QPS logging performance"""
    events = [
        {
            "event": "tool_execution",
            "payload": {
                "tool": "generate_response",
                "latency_ms": random.randint(100, 1000),
                "tokens": random.randint(50, 500)
            }
        }
        for _ in range(1000)
    ]

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post("http://localhost:8114/log", json=event)
            for event in events
        ]
        await asyncio.gather(*tasks)

    end_time = time.time()
    qps = len(events) / (end_time - start_time)
    assert qps > 500  # Should handle >500 QPS

def test_cache_ttl():
    """Test cache TTL functionality"""
    # Set cache with TTL
    response = client.post("/cache/set", json={
        "key": "test_key",
        "data": {"value": "test"},
        "ttl": 2  # 2 seconds
    })
    assert response.status_code == 200

    # Verify cache exists
    response = client.get("/cache/get?key=test_key")
    assert response.status_code == 200
    assert response.json()["hit"] == True

    # Wait for TTL to expire
    time.sleep(3)

    # Verify cache expired
    response = client.get("/cache/get?key=test_key")
    assert response.status_code == 200
    assert response.json()["hit"] == False

def test_pii_redaction():
    """Test PII redaction functionality"""
    event = {
        "event": "user_action",
        "payload": {
            "user_id": "user123",
            "email": "test@example.com",
            "api_key": "sk-1234567890abcdef",
            "message": "Hello world"
        }
    }

    response = client.post("/log", json=event)
    assert response.status_code == 200

    result = response.json()
    assert "user_id" in result["redacted_fields"]
    assert "email" in result["redacted_fields"]
    assert "api_key" in result["redacted_fields"]
```

## Monitoring and Alerting

### Key Alerts

- **High Latency**: TTFB > 2 seconds for 5 minutes
- **Low Cache Hit Rate**: Cache hit rate < 70% for 10 minutes
- **High Error Rate**: > 5% of requests failing
- **PII Detection**: PII found in logs (should be zero)

### Dashboard Metrics

- **Request Rate**: Requests per second by endpoint
- **Latency Distribution**: P95, P99 latency percentiles
- **Cache Performance**: Hit rate, miss rate, eviction rate
- **Error Rate**: 4xx/5xx error percentages
- **Storage Usage**: Redis memory usage, log volume

## Future Enhancements

- **Distributed Tracing**: OpenTelemetry integration
- **Advanced Analytics**: ML-based anomaly detection
- **Custom Metrics**: User-defined KPI tracking
- **Multi-region**: Global telemetry aggregation
- **Real-time Dashboards**: Live metrics visualization
- **Audit Trails**: Immutable log storage with blockchain
