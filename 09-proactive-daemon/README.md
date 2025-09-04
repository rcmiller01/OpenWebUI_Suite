# Proactive Daemon

A cron/worker service that sends agent-initiated nudges to the OpenWebUI Pipelines Gateway based on various triggers.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure triggers:**
   Edit `config/triggers.yaml` to enable/disable triggers and set parameters.

3. **Set environment variables:**
   ```bash
   export PIPELINES_SYSTEM_TOKEN="your_system_token_here"
   ```

4. **Run in dry-run mode first:**
   ```bash
   python src/worker.py --config config/triggers.yaml --dry-run --once
   ```

5. **Run continuously:**
   ```bash
   python src/worker.py --config config/triggers.yaml
   ```

## Configuration

The daemon is configured via `config/triggers.yaml`. Key settings:

- **pipelines_url**: URL of the Pipelines Gateway
- **system_token**: Authentication token for system messages
- **dry_run**: Set to true to log actions without sending messages
- **Triggers**: Enable/disable specific trigger types

## Trigger Types

### Time-of-Day
- Sends scheduled messages at specific times (e.g., morning briefing, evening summary)
- Configurable schedule and message templates

### Inactivity Gap
- Monitors user activity and sends reminders after periods of inactivity
- Configurable threshold in minutes

### OpenBB Alerts
- Monitors financial market data for significant price movements
- Configurable symbols, thresholds, and alert messages

### Tandoor Gaps
- Checks meal planning status and sends reminders
- Integrates with Tandoor Recipes API

### Drive Anomalies
- Monitors driving patterns for safety concerns
- Configurable anomaly detection thresholds

## Running as a Service

### Cron Job
Add to crontab for periodic execution:
```bash
*/15 * * * * /path/to/venv/bin/python /path/to/worker.py --once
```

### Systemd Service
Create `/etc/systemd/system/proactive-daemon.service`:
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

## Testing

Run the test suite:
```bash
python test_daemon.py
```

This will test:
- Configuration loading
- Idempotency functionality
- Dry-run mode

## Idempotency

The daemon uses idempotency keys to prevent duplicate messages:
- Keys are stored in SQLite database
- Configurable TTL (time-to-live)
- Automatic cleanup of expired keys

## Backoff Strategy

Failed API calls use exponential backoff:
- Initial delay: 1 second
- Multiplier: 2x per retry
- Maximum delay: 60 seconds
- Maximum retries: 5

## Logging

Comprehensive logging includes:
- Trigger execution results
- API call success/failure
- Idempotency key operations
- Configuration changes

## Development

### Adding New Triggers

1. Add trigger configuration to `config/triggers.yaml`
2. Implement trigger check method in `ProactiveDaemon` class
3. Call the method from `run_once()`
4. Update idempotency key generation if needed

### Testing New Triggers

Use dry-run mode to test new triggers without sending actual messages:
```bash
python src/worker.py --dry-run --once
```

## Troubleshooting

### Common Issues

1. **Configuration not found**: Ensure `config/triggers.yaml` exists and is readable
2. **Authentication failed**: Check `PIPELINES_SYSTEM_TOKEN` environment variable
3. **Database errors**: Ensure write permissions for SQLite database file
4. **API timeouts**: Check network connectivity to Pipelines Gateway

### Debug Mode

Enable verbose logging:
```bash
python src/worker.py --verbose --once
```
