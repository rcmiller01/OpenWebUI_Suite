# Pipelines Gateway Agent

## Goal
Stand up the central OpenAI-compatible Pipelines server (no forking Open WebUI). Hosts pre/post hooks, routing, memory calls, helpers/merge, drive state, tool registry.

## Scope

### Core Features
- ✅ Expose `/v1/chat/completions` (OpenAI-compatible)
- ✅ Plugin architecture: pre, mid, post hooks
- ✅ Registry for lanes, tools, models (local + OpenRouter)
- ✅ Stream single consolidated answer

### API (in/out)

- ✅ `POST /v1/chat/completions` (non-stream)
- ✅ `POST /v1/chat/completions/stream` (line-delimited JSON stream)
- ✅ `GET /v1/models` (simple model list)
- ✅ `GET /v1/tools` (tool schema list)
- ✅ `GET /metrics` (Prometheus-style counters)
- ✅ `POST /tasks/enqueue` (enqueue background pipeline task)
- ✅ `GET /tasks/dlq` (dead-letter queue items)
- ✅ Internal pipeline context enrichment (intent, memory, affect, drive, policy)

### Environment Variables

- Core Routing / Models:
  - `OPENROUTER_API_KEY` – API key for OpenRouter
  - `OPENROUTER_MODEL` – Default remote model
  - `DEFAULT_LOCAL_MODEL` – Local (Ollama) model id
- Observability:
  - `ENABLE_OTEL` (true/false)
  - `OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OTEL_SERVICE_NAME`
- Rate Limiting / Performance:
  - `RATE_LIMIT_PER_MIN` – refill rate (tokens/min)
  - `RATE_LIMIT_BURST` – bucket capacity (defaults to rate)
  - `PIPELINE_TIMEOUT_SECONDS` – hard timeout for chat requests
- Queue / Redis:
  - `REDIS_URL` – redis connection URL
  - `TASK_WORKER_ENABLED` – enable internal worker loop
  - `TASK_QUEUE_NAME` / `TASK_DQL_NAME`
- Security:
  - `SUITE_SHARED_SECRET` – optional HMAC signing for inter-service calls
- Misc:
  - `LOG_LEVEL`, `HOST`, `PORT`

## Project Structure

```
00-pipelines-gateway/
├── src/
│   ├── server.py              # Main FastAPI application
│   ├── hooks/
│   │   ├── pre/__init__.py    # Pre-processing hooks
│   │   ├── mid/__init__.py    # Mid-processing hooks
│   │   └── post/__init__.py   # Post-processing hooks
│   ├── router/
│   │   └── model_map.py       # Model routing and mapping
│   └── tools/
│       └── registry.py        # Tool registry and execution
├── config/
│   ├── models.json           # Model configurations
│   └── tools.json            # Tool configurations
├── tests/
│   └── test_gateway.py       # Test suite
├── requirements.txt          # Python dependencies
└── AGENT.md                 # This file
```

## Installation & Setup

### 1. Create Virtual Environment




```bash
cd 00-pipelines-gateway
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export OPENROUTER_API_KEY="your_openrouter_key_here"
export LOG_LEVEL="DEBUG"  # Optional: for development
```

### 4. Start the Server

```bash
uvicorn src.server:app --reload --port 8088 --host 0.0.0.0
```

## Usage Examples

### Basic Chat Completion

```bash
curl -X POST "http://localhost:8088/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mock-model",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "stream": false
  }'
```

### Streaming Chat Completion

```bash
curl -X POST "http://localhost:8088/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mock-model",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true
  }'
```

### List Available Models

```bash
curl "http://localhost:8088/v1/models"
```

### List Available Tools

```bash
curl "http://localhost:8088/v1/tools"
```

### Health Check

```bash
curl "http://localhost:8088/health"
```

### Metrics

```bash
curl "http://localhost:8088/metrics"
```

### Enqueue Background Task

```bash
curl -X POST "http://localhost:8088/tasks/enqueue" -H 'Content-Type: application/json' -d '{"messages":[{"role":"user","content":"Process later"}]}'
```

### Dead Letter Queue

```bash
curl "http://localhost:8088/tasks/dlq"
```

## Hook System

The gateway implements a 3-stage hook system:

### Pre-hooks (`src/hooks/pre/__init__.py`)
- User authentication and authorization
- Input validation and sanitization
- Intent detection from messages
- User memory and context loading

### Mid-hooks (`src/hooks/mid/__init__.py`)
- Tool selection based on intent
- Model parameter tuning
- Context enrichment with metadata

### Post-hooks (`src/hooks/post/__init__.py`)
- Response filtering and validation
- Analytics and metrics logging
- User memory updates
- Feedback collection

## Model Router

The model router (`src/router/model_map.py`) provides:

- **Model Discovery**: Automatic loading from `config/models.json`
- **Intelligent Routing**: Route requests to appropriate models based on intent
- **Provider Support**: OpenRouter, Ollama, local models
- **Fallback Handling**: Graceful degradation when models are unavailable

### Supported Providers
- **OpenRouter**: Cloud models via API
- **Ollama**: Local models via HTTP API
- **Local**: Mock models for development

## Tool Registry

The tool registry (`src/tools/registry.py`) manages:

- **Built-in Tools**: Calculator, web search
- **External Tools**: Configurable via `config/tools.json`
- **Tool Execution**: Safe execution with error handling
- **Tool Discovery**: OpenAI function format compatibility

### Built-in Tools
- **Calculator**: Basic mathematical operations
- **Web Search**: Mock web search functionality

## Testing

### Run Tests
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing
```bash
# Start server
uvicorn src.server:app --reload --port 8088

# Test streaming
curl -X POST "http://localhost:8088/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "mock-model", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

## Development

### Hot Reload
The server supports hot reload during development:
```bash
uvicorn src.server:app --reload --port 8088
```

### Adding New Hooks
1. Add functions to appropriate hook modules
2. Call them from the main hook runners
3. Update tests to verify functionality

### Adding New Tools
1. Create tool class inheriting from `Tool`
2. Implement `execute` method
3. Register in `ToolRegistry.load_config()`

### Adding New Models
1. Update `config/models.json` with model configuration
2. Implement provider support in `ModelRouter`
3. Test routing and execution

## Configuration

### Models Configuration (`config/models.json`)
```json
{
  "models": {
    "model-name": {
      "provider": "openrouter|ollama|local",
      "model_id": "provider/model-id",
      "max_tokens": 4096,
      "cost_per_token": 0.001,
      "capabilities": ["chat", "streaming"]
    }
  }
}
```

### Tools Configuration (`config/tools.json`)
```json
{
  "built_in_tools": ["calculator", "web_search"],
  "external_tools": [
    {
      "name": "tool-name",
      "description": "Tool description",
      "module": "tools.module_name",
      "enabled": true
    }
  ]
}
```

## Monitoring & Observability

### Logging
- Structured logging with request IDs
- Configurable log levels
- Performance and error tracking

### Health Checks
- `/health` endpoint for service monitoring
- Component status reporting
- Dependency health verification

### Metrics
- Request/response analytics
- Model usage tracking
- Tool execution statistics

## Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8088
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8088"]
```

### Environment Variables
```bash
OPENROUTER_API_KEY=your_production_key
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8088
```

### Scaling
- Stateless design enables horizontal scaling
- Model routing supports load balancing
- Tool execution can be distributed

## Security

### Input Validation
- Request payload validation with Pydantic
- Content filtering in pre-hooks
- Safe tool execution sandbox

### Rate Limiting
- Per-user request limits
- Per-model usage quotas
- Tool execution throttling

### Authentication
- Bearer token support
- User identification and permissions
- Audit logging

## Integration

### OpenWebUI Integration
The gateway is designed to work seamlessly with OpenWebUI:
```bash
# Point OpenWebUI to the gateway
export OPENAI_API_BASE="http://localhost:8088/v1"
export OPENAI_API_KEY="your-api-key"
```

### Third-party Integration
- OpenAI-compatible API ensures broad compatibility
- Webhook support for external services
- Plugin architecture for custom integrations

---

**Status**: ✅ Implemented and tested  
**Version**: 1.0.0  
**Last Updated**: September 3, 2025
