# Telemetry Cache Service

A high-performance telemetry caching and logging service for the OpenWebUI Suite with PII redaction, structured logging, and Prometheus metrics.

## Features

- **Structured Logging**: Async logging with JSON formatting and Loki integration
- **PII Redaction**: Automatic detection and redaction of sensitive data
- **Redis Caching**: High-performance caching with TTL support
- **Prometheus Metrics**: Comprehensive metrics collection and monitoring
- **FastAPI Backend**: RESTful API with automatic OpenAPI documentation
- **Health Monitoring**: Built-in health checks and service discovery

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f telemetry-cache

# Stop services
docker-compose down
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if not using Docker)
redis-server

# Start the service
python start.py
```

## API Endpoints

### Log Event

```http
POST /log
Content-Type: application/json

{
  "event": "tool_execution",
  "payload": {
    "tool": "generate_response",
    "latency_ms": 250,
    "tokens": 150,
    "user_id": "user123"
  }
}
```

### Cache Operations

```http
POST /cache/set
Content-Type: application/json

{
  "key": "tool_cache_key",
  "data": {"response": "cached data"},
  "ttl": 3600
}

GET /cache/get?key=tool_cache_key
```

### Health Check

```http
GET /health
```

### Metrics

```http
GET /metrics
```

## Configuration

Environment Variables:

- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379)
- `PROMETHEUS_PORT`: Prometheus metrics port (default: 9090)
- `LOG_LEVEL`: Logging level (default: INFO)
- `TELEMETRY_CACHE_VERSION`: Service version (default: 1.0.0)

## Monitoring

### Prometheus Metrics

- `telemetry_cache_ttfb_seconds`: Time-to-first-byte histogram
- `telemetry_cache_tokens_per_second`: Token processing rate
- `telemetry_cache_repair_rate_total`: Error repair counter
- `telemetry_cache_cache_hits_total`: Cache hit counter
- `telemetry_cache_cache_misses_total`: Cache miss counter

### Grafana Dashboard

Access Grafana at `http://localhost:3000` (admin/admin) to visualize metrics.

## Testing

```bash
# Run unit tests
python -m pytest test_api.py -v

# Run with coverage
python -m pytest test_api.py --cov=src --cov-report=html
```

## Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenWebUI     │───▶│ Telemetry Cache │───▶│     Redis       │
│   Services      │    │   Service       │    │   Cache Store   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Prometheus    │
                       │   Metrics       │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Grafana     │
                       │   Dashboards    │
                       └─────────────────┘
```

## Security

- Automatic PII detection and redaction
- Structured logging prevents sensitive data leakage
- Redis authentication support
- Container security best practices

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# View API documentation
open http://localhost:8000/docs
```

## License

MIT License - see LICENSE file for details.
