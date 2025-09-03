# OpenWebUI Suite Deployment

A meta-repository for deploying OpenWebUI with a comprehensive plugin system.

## Quick Start

Deploy the complete OpenWebUI Suite with one command:

```bash
OLLAMA_HOST=http://core2-gpu:11434 docker compose -f compose/docker-compose.yaml up -d
```

## What's Included

This deployment includes:

- **OpenWebUI Core**: Base application with extension system
- **Ollama Tools Plugin**: Model management, health checks, routing, memory storage
- **Template Plugin**: Development reference implementation
- **Template Widget**: Frontend widget example
- **Admin Interface**: Plugin management and monitoring

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenWebUI     │    │     Plugins      │    │    Widgets      │
│      Core       │◄───┤                  │    │                 │
│                 │    │ • Ollama Tools   │    │ • Template      │
│ • Extension     │    │ • Template       │    │ • Custom        │
│   Loader        │    │ • Custom         │    │                 │
│ • Admin Panel   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Docker      │
                    │   Composition   │
                    │                 │
                    │ • Web UI        │
                    │ • Ollama        │
                    │ • Storage       │
                    └─────────────────┘
```

## Repository Structure

```
openwebui-suite/
├── manifests/           # Version pinning and configuration
│   └── release-2025.09.03.yaml
├── compose/            # Docker Compose configurations
│   └── docker-compose.yaml
├── docker/             # Docker build files
│   └── Dockerfile
├── scripts/            # Deployment and management scripts
│   └── freeze.sh
└── .github/workflows/  # CI/CD automation
```

## Components

### Core Application
- **Repository**: `openwebui-core`
- **Base**: Fork of open-webui/open-webui
- **Extensions**: Plugin loader, widget system, admin interface

### Plugins
- **Ollama Tools** (`owui-plugin-ollama-tools`): Production-ready Ollama integration
- **Template** (`owui-plugin-template`): Development reference

### Widgets
- **Template** (`owui-widget-template`): Frontend component example

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://core2-gpu:11434` | Ollama server endpoint |
| `OWUI_MEMORY_PATH` | `/data/memory.sqlite` | Plugin data storage |
| `OWUI_PLUGIN_TIMEOUT` | `30` | Plugin operation timeout |
| `WEBUI_AUTH` | `true` | Enable authentication |
| `LOG_LEVEL` | `INFO` | Logging level |

### Docker Compose Profiles

```bash
# Basic deployment (WebUI only)
docker compose up -d

# Include Ollama service
docker compose --profile ollama up -d

# Include Redis caching
docker compose --profile redis up -d

# Include PostgreSQL database
docker compose --profile postgres up -d

# Full production stack
docker compose --profile ollama --profile redis --profile postgres up -d
```

## Deployment Options

### 1. Quick Start (SQLite)
```bash
git clone <repo>
cd openwebui-suite
OLLAMA_HOST=http://your-ollama:11434 docker compose up -d
```

### 2. Production (PostgreSQL + Redis)
```bash
# Set environment variables
export POSTGRES_PASSWORD=secure-db-password
export REDIS_PASSWORD=secure-redis-password
export WEBUI_SECRET_KEY=your-secret-key

# Deploy with production services
docker compose --profile postgres --profile redis up -d
```

### 3. Development
```bash
# Clone all repositories
git clone <core-repo> openwebui-core
git clone <plugin-repo> owui-plugin-ollama-tools
# ... other repos

# Use local development images
export COMPOSE_FILE=compose/docker-compose.dev.yaml
docker compose up -d
```

## API Endpoints

Once deployed, the following endpoints are available:

### Core Application
- `GET /` - Web interface
- `GET /health` - Application health
- `GET /admin` - Admin interface

### Ollama Plugin
- `GET /ext/ollama/health` - Ollama service status
- `GET /ext/ollama/models` - Available models
- `POST /ext/ollama/route` - Model routing
- `POST /ext/ollama/memory/set` - Store data
- `GET /ext/ollama/memory/get` - Retrieve data

### Template Plugin
- `GET /ext/template/health` - Plugin status
- `GET /ext/template/info` - Plugin information

## Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:3000/health

# Plugin health
curl http://localhost:3000/ext/ollama/health
curl http://localhost:3000/ext/template/health
```

### Logs
```bash
# Application logs
docker compose logs webui

# All services
docker compose logs

# Follow logs
docker compose logs -f webui
```

### Metrics
Access the admin interface at http://localhost:3000/admin for:
- Plugin status and metrics
- Resource usage
- Error tracking
- Configuration management

## Updating

### Update to Latest Release
```bash
# Pull latest manifest
git pull origin main

# Update deployment
docker compose down
docker compose pull
docker compose up -d
```

### Update Specific Components
```bash
# Update only the core application
docker compose pull webui
docker compose up -d webui

# Update and restart specific services
docker compose up -d --force-recreate webui
```

## Troubleshooting

### Common Issues

1. **Plugin Load Failures**
   ```bash
   # Check plugin logs
   docker compose logs webui | grep plugin
   
   # Verify plugin installation
   docker compose exec webui pip list | grep owui
   ```

2. **Ollama Connection Issues**
   ```bash
   # Test Ollama connectivity
   curl $OLLAMA_HOST/api/tags
   
   # Check network connectivity
   docker compose exec webui curl $OLLAMA_HOST/api/tags
   ```

3. **Database Issues**
   ```bash
   # Check database logs
   docker compose logs postgres
   
   # Test database connection
   docker compose exec postgres psql -U openwebui -d openwebui -c "SELECT 1;"
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export OWUI_DEBUG=true

# Restart with debug logging
docker compose down
docker compose up -d
```

## Security

### Production Security Checklist

- [ ] Set strong `WEBUI_SECRET_KEY`
- [ ] Use strong database passwords
- [ ] Enable HTTPS with reverse proxy
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Backup encryption

### Network Security
```yaml
# Use with reverse proxy (nginx, traefik, etc.)
services:
  webui:
    expose:
      - "3000"  # Don't expose to host
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.webui.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.webui.tls=true"
```

## Backup and Recovery

### Data Backup
```bash
# Backup data volume
docker compose exec webui tar czf /data/backup.tar.gz /data

# Copy backup to host
docker cp openwebui-suite:/data/backup.tar.gz ./backup.tar.gz
```

### Database Backup
```bash
# PostgreSQL backup
docker compose exec postgres pg_dump -U openwebui openwebui > backup.sql

# SQLite backup (if using default)
docker cp openwebui-suite:/data/memory.sqlite ./memory.sqlite.backup
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with development compose
5. Submit a pull request

## Support

- **Documentation**: [GitHub Wiki](https://github.com/<ORG>/openwebui-suite/wiki)
- **Issues**: [GitHub Issues](https://github.com/<ORG>/openwebui-suite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/<ORG>/openwebui-suite/discussions)

---

**Version**: 2025.09.03  
**Last Updated**: September 3, 2025  
**License**: MIT
