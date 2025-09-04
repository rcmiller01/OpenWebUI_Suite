# 15-ByteBot-Gateway

Secure desktop automation gateway service for the OpenWebUI Suite, providing a safe "super-tool" interface for ByteBot with plan → confirm → execute workflow.

## Features

- **Secure Desktop Automation**: Safe execution of desktop automation tasks through ByteBot
- **Plan-Confirm-Execute Workflow**: Three-stage process ensuring user control and safety
- **HMAC Signature Verification**: Cryptographic request authentication and integrity
- **Capability-Based Security**: Granular permission system with allow-lists
- **Real-Time Event Streaming**: Server-Sent Events for live task monitoring
- **REST API**: FastAPI-based endpoints with comprehensive error handling
- **Container Ready**: Docker deployment with health checks and security best practices

## Quick Start

### Using Docker Compose

```bash
# Clone and navigate to the service directory
cd 15-bytebot-gateway

# Start the service
docker-compose up -d

# Check health
curl http://localhost:8089/health
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python start.py

# Or use the shell script
./start.sh
```

## API Usage

### Health Check

```bash
curl http://localhost:8089/health
```

Response:

```json
{
  "status": "healthy",
  "service": "bytebot-gateway",
  "version": "1.0.0"
}
```

### Get Capabilities

```bash
curl http://localhost:8089/capabilities
```

Response:
```json
{
  "capabilities": {
    "fs.read": {
      "enabled": true,
      "risk_level": "low",
      "description": "Read file contents"
    },
    "fs.write": {
      "enabled": true,
      "risk_level": "medium",
      "description": "Write file contents"
    }
  }
}
```

### Plan Action

```bash
curl -X POST http://localhost:8089/plan \
  -H "Content-Type: application/json" \
  -H "X-Timestamp: $(date +%s%3N)" \
  -H "X-Signature: <hmac-signature>" \
  -d '{
    "action": "fs.read",
    "parameters": {
      "path": "/tmp/test.txt"
    }
  }'
```

Response:
```json
{
  "task_id": "task_abc123",
  "action": "fs.read",
  "parameters": {
    "path": "/tmp/test.txt"
  },
  "estimated_risk": "low",
  "plan_summary": "Read contents of /tmp/test.txt",
  "requires_confirmation": true
}
```

### Execute Action

```bash
curl -X POST http://localhost:8089/execute \
  -H "Content-Type: application/json" \
  -H "X-Timestamp: $(date +%s%3N)" \
  -H "X-Signature: <hmac-signature>" \
  -d '{
    "task_id": "task_abc123",
    "action": "fs.read",
    "parameters": {
      "path": "/tmp/test.txt"
    }
  }'
```

Response:
```json
{
  "task_id": "task_abc123",
  "status": "running",
  "message": "Task execution started"
}
```

### Event Streaming

```bash
curl http://localhost:8089/events
```

Server-Sent Events stream:
```
data: {"event": "task_started", "task_id": "task_abc123", "timestamp": "2024-01-01T12:00:00Z"}

data: {"event": "task_progress", "task_id": "task_abc123", "progress": 50, "message": "Processing..."}

data: {"event": "task_completed", "task_id": "task_abc123", "result": {"content": "file contents..."}}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `SHARED_SECRET` | Required | HMAC signature verification key |
| `BYTEBOT_URL` | `http://localhost:3000` | ByteBot API endpoint URL |
| `BYTEBOT_API_KEY` | Required | ByteBot API authentication key |
| `WORKDIR` | `/tmp/bytebot-workdir` | Working directory for file operations |
| `MAX_FILE_SIZE_MB` | `10` | Maximum file size for operations |
| `REQUEST_TIMEOUT` | `30` | Request timeout in seconds |
| `RETRY_ATTEMPTS` | `3` | Number of retry attempts for failed requests |

### Policy Configuration

The `config/policy.json` file defines capability allow-lists:

```json
{
  "capabilities": {
    "fs.read": {
      "enabled": true,
      "risk_level": "low",
      "max_file_size_mb": 10,
      "allowed_paths": ["/tmp", "/home/user"]
    },
    "browser.open": {
      "enabled": true,
      "risk_level": "medium",
      "allowed_domains": ["localhost", "*.example.com"]
    }
  },
  "security": {
    "require_signature": true,
    "signature_tolerance_ms": 300000,
    "max_concurrent_tasks": 5
  }
}
```

### ByteBot Configuration

The `config/bytebot.json` file contains ByteBot connection settings:

```json
{
  "url": "http://localhost:3000",
  "api_key": "your-bytebot-api-key",
  "timeout": 30,
  "retry_attempts": 3,
  "workdir": "/tmp/bytebot-workdir"
}
```

## Security Features

### HMAC Signature Verification

All API requests require HMAC-SHA256 signature authentication:

```python
import hmac
import hashlib
import base64
import json
import time

def generate_signature(payload, timestamp, secret):
    message = f"{timestamp}:{json.dumps(payload, separators=(',', ':'))}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

# Usage
payload = {"action": "fs.read", "parameters": {"path": "/tmp/test.txt"}}
timestamp = str(int(time.time() * 1000))
signature = generate_signature(payload, timestamp, "your-shared-secret")
```

### Capability-Based Access Control

- **Granular Permissions**: Each capability can be individually enabled/disabled
- **Risk Assessment**: Actions are categorized by risk level (low, medium, high)
- **Path Restrictions**: File operations limited to allowed directories
- **Domain Restrictions**: Browser operations limited to approved domains

### Sandbox Environment

- **Isolated Working Directory**: All file operations confined to designated workdir
- **Non-Root Execution**: Service runs as unprivileged user
- **Resource Limits**: File size and concurrent task restrictions

## Integration with OpenWebUI Pipelines

The ByteBot Gateway integrates with OpenWebUI Pipelines through the pipelines-gateway service:

```python
# Example pipeline integration
from pipelines import Pipeline

pipeline = Pipeline()

@pipeline.tool()
def desktop_automation(action: str, parameters: dict):
    """Execute desktop automation through ByteBot Gateway"""
    import requests
    import hmac
    import hashlib
    import base64
    import json
    import time

    # Generate HMAC signature
    payload = {"action": action, "parameters": parameters}
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(payload, timestamp, SHARED_SECRET)

    # Plan phase
    plan_response = requests.post(
        "http://localhost:8089/plan",
        json=payload,
        headers={
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }
    )

    if plan_response.status_code == 200:
        plan_data = plan_response.json()
        task_id = plan_data["task_id"]

        # Execute phase (after user confirmation)
        execute_response = requests.post(
            "http://localhost:8089/execute",
            json={"task_id": task_id, **payload},
            headers={
                "X-Timestamp": str(int(time.time() * 1000)),
                "X-Signature": generate_signature(
                    {"task_id": task_id, **payload},
                    str(int(time.time() * 1000)),
                    SHARED_SECRET
                )
            }
        )

        return execute_response.json()

    return plan_response.json()
```

## Testing

Run the comprehensive test suite:

```bash
python test_api.py
```

This will test:

- Health endpoint
- Capabilities endpoint
- Plan endpoint with HMAC signatures
- Execute endpoint
- Event streaming
- Invalid signature rejection

## Development

### Project Structure

```text
15-bytebot-gateway/
├── src/
│   ├── app.py                 # Main FastAPI application
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── bytebot_http.py    # ByteBot HTTP adapter
│   └── __init__.py
├── config/
│   ├── policy.json            # Capability policies
│   └── bytebot.json           # ByteBot configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Container orchestration
├── start.py                   # Python startup script
├── start.sh                   # Shell startup script
├── test_api.py               # API test suite
└── README.md                 # This file
```

### Adding New Capabilities

1. Update `config/policy.json` with new capability definition
2. Implement capability validation in `src/app.py`
3. Add capability handling in ByteBot adapter if needed
4. Update tests in `test_api.py`

## Deployment

### Production Considerations

- **Change Default Secrets**: Update `SHARED_SECRET` and `BYTEBOT_API_KEY`
- **Configure ByteBot URL**: Set correct ByteBot service endpoint
- **Set Resource Limits**: Configure file size and concurrency limits
- **Enable HTTPS**: Use reverse proxy for SSL termination
- **Monitor Logs**: Set up log aggregation and alerting
- **Backup Configuration**: Regularly backup policy and configuration files

### Docker Production Deployment

```yaml
version: '3.8'
services:
  bytebot-gateway:
    image: bytebot-gateway:latest
    environment:
      - LOG_LEVEL=WARNING
      - SHARED_SECRET=${BYTEBOT_SHARED_SECRET}
      - BYTEBOT_API_KEY=${BYTEBOT_API_KEY}
    secrets:
      - bytebot_shared_secret
      - bytebot_api_key
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## Troubleshooting

### Common Issues

#### HMAC Signature Errors

- Verify `SHARED_SECRET` is consistent between client and server
- Check timestamp is within tolerance window (5 minutes default)
- Ensure payload is JSON serialized with consistent formatting

#### Capability Denied

- Check `config/policy.json` has the capability enabled
- Verify risk level allows the operation
- Confirm path/domain restrictions are satisfied

#### ByteBot Connection Failed

- Verify `BYTEBOT_URL` is accessible
- Check `BYTEBOT_API_KEY` is valid
- Review ByteBot service logs for connection issues

#### Event Streaming Issues

- Ensure client supports Server-Sent Events
- Check for network connectivity issues
- Verify CORS settings allow the requesting domain

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python start.py
```

## License

This service is part of the OpenWebUI Suite. See project license for details.
