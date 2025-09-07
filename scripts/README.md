# Production Deployment Scripts

This directory contains scripts and configuration files for production deployment of the OpenWebUI Suite.

## Files

### `owui_sanity.sh`
Comprehensive health check script that verifies:
- Docker Compose configuration validity
- Service container status
- DNS resolution within the Docker network
- HTTP health endpoints for all services
- Network connectivity

**Usage:**
```bash
# Default network and compose file
./scripts/owui_sanity.sh

# Custom network
NET=my_network ./scripts/owui_sanity.sh
```

### `../systemd/owui.service`
Systemd service unit for automatic startup and management.

**Installation:**
```bash
# Copy service file
sudo cp systemd/owui.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable owui.service

# Start service
sudo systemctl start owui.service

# Check status
sudo systemctl status owui.service
```

## Environment Variables

### Sanity Script
- `NET`: Docker network name (default: `root_owui`)
- `COMPOSE_FILE`: Path to compose file (default: `/root/compose.prod.yml`)

### Systemd Service
- `OWUI_NETWORK`: Docker network name (default: `root_owui`)
- `COMPOSE_PROFILES`: Active profiles (default: `extras,ui`)

## Production Checklist

1. **Pre-deployment:**
   - [ ] Copy `compose.prod.yml` to `/root/`
   - [ ] Ensure Docker and Docker Compose are installed
   - [ ] Create necessary directories (`/data`, `/logs`, etc.)
   - [ ] Set up SSL certificates if using HTTPS
   - [ ] Configure firewall rules

2. **Deployment:**
   - [ ] Run sanity check: `./scripts/owui_sanity.sh`
   - [ ] Install systemd service
   - [ ] Enable auto-start: `sudo systemctl enable owui.service`
   - [ ] Start services: `sudo systemctl start owui.service`

3. **Post-deployment:**
   - [ ] Verify all services are healthy
   - [ ] Check logs for errors
   - [ ] Test external connectivity
   - [ ] Set up monitoring/alerting
   - [ ] Configure backup procedures

## Troubleshooting

### Service Won't Start
```bash
# Check systemd logs
sudo journalctl -u owui.service -f

# Check compose logs
docker compose -f /root/compose.prod.yml logs

# Validate compose file
docker compose -f /root/compose.prod.yml config
```

### Health Checks Failing
```bash
# Run sanity check
./scripts/owui_sanity.sh

# Check individual service health
docker compose -f /root/compose.prod.yml ps
docker compose -f /root/compose.prod.yml logs gateway
```

### Network Issues
```bash
# Verify network exists
docker network ls | grep owui

# Recreate network if needed
docker network rm root_owui
docker network create root_owui
```

## Security Considerations

- Service runs as root (required for Docker access)
- Ensure compose file permissions are restrictive
- Use Docker secrets for sensitive data
- Consider running behind a reverse proxy
- Regular security updates for base images

## Monitoring

The sanity script can be run periodically via cron:

```bash
# Add to crontab (check every 5 minutes)
*/5 * * * * /path/to/owui_sanity.sh >/dev/null 2>&1 || /usr/bin/logger "OWUI health check failed"
```
