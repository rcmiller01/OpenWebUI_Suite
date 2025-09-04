# 09-Proactive Daemon

## Goal
Cron/worker service to send agent-initiated nudges to Pipelines Gateway. This daemon proactively monitors various triggers and sends contextual messages to keep the AI assistant engaged and helpful.

## Architecture

### Triggers
- **Time-of-day**: Scheduled nudges at specific times (morning briefing, evening summary)
- **Inactivity gap**: Detects periods of user inactivity and sends gentle reminders
- **OpenBB alerts**: Financial market alerts and notifications
- **Tandoor gaps**: Recipe/meal planning reminders and suggestions
- **Drive anomalies**: Unusual driving patterns or safety concerns

### Actions
- POST to Pipelines `/v1/chat/completions` with system token
- Append contextual messages based on trigger type
- Support dry-run mode for testing

### Key Features
- **Idempotency**: Keys per trigger to prevent duplicate nudges
- **Backoff**: Exponential backoff on API failures
- **Configurable**: YAML-based trigger configuration
- **Logging**: Comprehensive logging for monitoring and debugging

## API Integration

### Pipelines Gateway
- **Endpoint**: `POST /v1/chat/completions`
- **Authentication**: System token for agent-initiated messages
- **Message Format**: Structured JSON with trigger context

### External Services
- **OpenBB**: Financial data and alerts
- **Tandoor**: Recipe and meal planning data
- **Drive State**: Driving pattern analysis

## Configuration

### triggers.yaml
```yaml
triggers:
  time_of_day:
    enabled: true
    schedule:
      - "08:00"  # Morning briefing
      - "18:00"  # Evening summary
    messages:
      morning: "Good morning! Here's your daily briefing..."
      evening: "Evening summary and tomorrow's outlook..."

  inactivity_gap:
    enabled: true
    threshold_minutes: 120
    message: "I noticed you haven't been active. Would you like me to..."

  openbb_alerts:
    enabled: true
    symbols: ["SPY", "QQQ", "BTC-USD"]
    thresholds:
      price_change: 0.05  # 5% change
    message: "Market alert: {symbol} has moved {change}%"

  tandoor_gaps:
    enabled: true
    check_interval: "1h"
    message: "Meal planning reminder: {suggestion}"

  drive_anomalies:
    enabled: true
    message: "Drive safety alert: {anomaly_type}"
```

## Usage

### Running as Cron Job
```bash
# Run every 15 minutes
*/15 * * * * /path/to/venv/bin/python /path/to/worker.py
```

### Running as Systemd Service
```ini
[Unit]
Description=Proactive Daemon
After=network.target

[Service]
Type=simple
User=proactive
ExecStart=/path/to/venv/bin/python /path/to/worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Manual Execution
```bash
# Dry run mode
python src/worker.py --dry-run

# Single execution
python src/worker.py --once

# Verbose logging
python src/worker.py --verbose
```

## Development Notes

### Idempotency Implementation
- Each trigger maintains a unique key based on trigger type and timestamp
- Keys stored in SQLite database with TTL
- Prevents duplicate messages within configurable time windows

### Error Handling
- Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, 60s max
- Circuit breaker pattern for external service failures
- Graceful degradation when services are unavailable

### Testing
- Dry-run mode logs all actions without sending messages
- Mock external services for unit testing
- Integration tests with Pipelines Gateway

## Dependencies
- requests: HTTP client for API calls
- pyyaml: Configuration file parsing
- schedule: Cron-like scheduling
- sqlite3: Local database for idempotency keys

## Monitoring
- Structured logging with trigger types and outcomes
- Health check endpoint for service monitoring
- Metrics collection for trigger success/failure rates</content>
<parameter name="filePath">c:\Users\rober\OneDrive\Documents\GitHub\OpenWebUI_Suite\09-proactive-daemon\AGENT.md
