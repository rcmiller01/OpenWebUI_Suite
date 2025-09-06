# OpenWebUI Suite

A comprehensive multi-repository project that creates a thin fork of OpenWebUI with a clean extension system, plugin templates, and deployment automation.

## Architecture Overview

This project consists of five interconnected repositories:

### 🔧 [openwebui-core](./openwebui-core/)

- **Purpose**: Thin fork of OpenWebUI with extension system
- **Features**: Backend/frontend extension loaders, minimal admin UI hooks
- **Goal**: Keep upstream merges easy while adding plugin capabilities

### 📦 [owui-plugin-template](./owui-plugin-template/)

- **Purpose**: Python plugin template for rapid development
- **Features**: Entry point configuration, test framework, CI/CD
- **Goal**: Standardized plugin development workflow

### 🎨 [owui-widget-template](./owui-widget-template/)

- **Purpose**: Frontend widget template for dynamic UI panels
- **Features**: React/TypeScript components, build system
- **Goal**: Consistent UI extension development

### 🛠️ [owui-plugin-ollama-tools](./owui-plugin-ollama-tools/)

- **Purpose**: First real plugin demonstrating Ollama integration
- **Features**: Model routing, health checks, simple memory store
- **Goal**: Reference implementation for plugin development

### 🚀 [openwebui-suite](./openwebui-suite/)

- **Purpose**: Meta repository for deployment and version management
- **Features**: Docker composition, version pinning, release automation
- **Goal**: Reproducible deployment across environments

## Quick Start

1. **Development Setup**
   ```bash
   # Clone and enter workspace
   git clone <this-repo>
   cd OpenWebUI_Suite
   
   # Each subdirectory is a separate repository
   # Initialize git remotes as needed
   ```

2. **Docker Deployment (Unified Compose)**

   ```bash
   # Build images
   make build

   # Start core profile (gateway + intent + merger + redis)
   make up PROFILE=core

   # Start full stack
   make up PROFILE=all

   # View services
   make ps

   # Tail logs for gateway
   make logs SERVICE=gateway
   ```

   Profiles available:
   - core (gateway, intent-router, merger, redis)
   - memory
   - affect (feeling-engine)
   - policy (policy guardrails)
   - tools (BYOF tools)
   - finance (OpenBB)
   - speech (stt-tts)
   - vision (multimodal-router, fastvlm)
   - telemetry (telemetry-cache)
   - extras (drive-state, proactive, tandoor, bytebot)
   - all (aggregate of the above)

3. **Development Mode**

   ```bash
   # Start each component separately for development
   cd openwebui-core && npm run dev &
   cd owui-plugin-ollama-tools && pip install -e . && python -m uvicorn main:app --reload
   ```

## Technology Stack

- **Backend**: FastAPI, Python 3.10+, SQLite
- **Frontend**: React, TypeScript, Tailwind CSS
- **Packaging**: setuptools entry points, GitHub Packages
- **Deployment**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

## Extension System

### Backend Plugins

- Use Python entry points with group `openwebui.plugins`
- Implement `register(app: FastAPI) -> None` function
- Auto-discovery via `importlib.metadata`

### Frontend Widgets

- Manifest-based widget loading
- Dynamic imports for runtime composition
- React component architecture

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://core2-gpu:11434` | Ollama server endpoint |
| `OWUI_MEMORY_PATH` | `./data/memory.sqlite` | Plugin memory store path |

## Development Workflow

1. **Plugin Development**: Start with `owui-plugin-template`
2. **Widget Development**: Use `owui-widget-template`
3. **Core Changes**: Minimize changes to `openwebui-core`
4. **Deployment**: Use unified `docker-compose.yml` with profiles
5. **Health Checks**: Every FastAPI service now exposes both `/health` and `/healthz`
6. **Dependency Consistency**: Python services install unpinned requirements constrained via root `constraints.txt` and a shared base Docker image layer for caching

## Release Process

1. Version plugins independently
2. Update `openwebui-suite/manifests/release-YYYY.MM.DD.yaml`
3. GitHub Actions builds and publishes suite image
4. Deploy with Docker Compose

## Contributing

- Keep core fork minimal
- All new features as plugins/widgets
- Fast CI (< 3 minutes)
- Environment-based configuration
- Comprehensive documentation
- Prefer adding new logic as plugins/sidecars instead of core changes
- Keep commits small and focused (feature, chore, fix)

## Operations Cheat Sheet

| Action | Command |
|--------|---------|
| Build all images | `make build` |
| Start core profile | `make up PROFILE=core` |
| Start everything | `make up PROFILE=all` |
| Stop & remove | `make down` |
| Validate compose | `make compose-validate` |
| Smoke tests | `make test` |
| Tail logs | `make logs SERVICE=gateway` |

Health endpoints (any service):

```text
GET /health    # JSON status (readiness)
GET /healthz   # Kubernetes-style minimal ok
```

## File Upload & Memory Integration (Gateway)

Gateway supports local file uploads (`/v1/files`) with snippet extraction and safe system prompt injection (length & MIME constrained). Force remote vs local model routing with headers:

```text
X-Force-Remote: true
X-Force-Local: true
```

Metrics counters include file uploads, snippet injections, and remote/local decision tallies.

## License

MIT License - see individual repositories for details.

---

**Date Created**: September 3, 2025  
**Status**: Development Setup Phase
