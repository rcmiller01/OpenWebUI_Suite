# OpenWebUI Suite ![CI](https://github.com/rcmiller01/OpenWebUI_Suite/actions/workflows/ci.yml/badge.svg)

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
| `GATEWAY_DB` | `/data/gateway.db` | Gateway projects database path |
| `ENABLE_PROJECTS` | `false` | Enable projects UI sidebar (set to `1` or `true`) |

## Development Workflow

1. **Plugin Development**: Start with `owui-plugin-template`
2. **Widget Development**: Use `owui-widget-template`
3. **Core Changes**: Minimize changes to `openwebui-core`
4. **Deployment**: Use unified `docker-compose.yml` with profiles
5. **Health Checks**: Every FastAPI service now exposes both `/health` and `/healthz`
6. **Dependency Consistency**: Python services install unpinned requirements constrained via root `constraints.txt` and a shared base Docker image (`owui/base:py311`) for caching
7. **CI Pipeline**: Automated GitHub Actions workflow validates dependency drift, tests, security, SBOM, coverage, and image builds
8. **Container Standards**: All FastAPI services share a unified Dockerfile pattern (base image, constraints install, `/healthz` healthcheck)
9. **Observability**: Optional telemetry profile adds Prometheus + Grafana + Loki + Promtail; `telemetry/prometheus.yml` scrapes all service ports
10. **Secrets Handling**: Runtime secrets mounted via Docker secrets (see `secrets/` placeholders); never commit real keys

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
| Build base image | `make base-build` |
| Start core profile | `make up PROFILE=core` |
| Start everything | `make up PROFILE=all` |
| Dev core (shortcut) | `make dev:core` |
| Dev all (shortcut) | `make dev:all` |
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

## Projects Feature (Gateway)

The gateway includes a lightweight projects system for organizing conversations:

- **Backend**: SQLite-based storage (`GATEWAY_DB` env var)
- **API**: REST endpoints at `/projects/*` for CRUD operations
- **Storage**: Volume mount at `/data` recommended for persistence
- **UI**: Optional sidebar component (feature flag `ENABLE_PROJECTS`)

Example usage:

```bash
# Create project
curl -X POST http://localhost:8088/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project"}'

# Add conversation to project
curl -X POST http://localhost:8088/projects/{project_id}/items \
  -H "Content-Type: application/json" \
  -d '{"convo_id":"conversation-uuid"}'

# List project conversations
curl http://localhost:8088/projects/{project_id}/items
```

For UI integration, set `ENABLE_PROJECTS=1` and import `ProjectsSidebar` component.

## License

MIT License - see individual repositories for details.

---

**Date Created**: September 3, 2025  
**Status**: Active Development (CI enabled)

## Continuous Integration

- Linting & Types: Configure via `.ruff.toml` and `mypy.ini` (ruff + mypy optional locally)

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on pushes and pull requests and includes:

- Dependency Drift Check: Ensures all services conform to `constraints.txt`.
- Test Suite: Fast subset of tests (skips heavy ML services by default).
- Heavy ML Tests: Opt-in via commit or PR title containing `[heavy]`.
- Security Audit: `pip-audit` vulnerability scan of resolved dependency set.
- Docker Build Matrix: Builds each service image (cache optimized, no push).
- Service Graph Validation: Ensures `SERVICE_GRAPH.mmd` edges match required architecture.
- SBOM Generation: CycloneDX SBOM (`sbom-python.xml`) artifact for dependency transparency.
- Coverage Reporting: Pytest coverage XML uploaded (Codecov optional if token configured).
- Heavy Model Cache: Caches HuggingFace / Whisper / Torch hubs for opt-in heavy tests.
- Release Image Publishing: On GitHub Release publishes service images to GHCR (`ghcr.io/<repo>/<service>:<tag>`).
- Lint & Types: Ruff + mypy pre-check gate.
- Dockerfile Lint: hadolint (blocking) on all Dockerfiles.
- Multi-Arch Release: Publish linux/amd64 & linux/arm64 images.
- GPU Variants: CUDA-tagged images (-cuda) built for heavy ML services on release.
- Image Signing & Attestation: Optional Cosign signing + CycloneDX SBOM attestation when key provided.
- SBOM Diff: SBOM changes against main uploaded as artifact.
- Image Size Reporting: Per-service size artifact for regression tracking.

### Image Optimization

Heavy ML services (`11-stt-tts-gateway`, `16-fastvlm-sidecar`) use a multi-stage layout splitting core vs. heavy model wheels for better layer reuse. Optional model prefetch layer warms model weights at build (ARG `PREFETCH_MODELS=true`) to reduce first-request latency. Multi-arch builds supported via:

`python scripts/build_all.py --multi-arch --tag <tag> [--push]`

CUDA variants are produced with tag suffix `-cuda` (linux/amd64) using `--build-arg BASE_IMAGE=nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04`.

Model prefetch examples:

```bash
# Prefetch STT + TTS models at build
docker build -t owui/stt-tts:prefetch --build-arg PREFETCH_MODELS=true 11-stt-tts-gateway

# Prefetch FastVLM model weights
docker build -t owui/fastvlm:prefetch --build-arg PREFETCH_MODELS=true 16-fastvlm-sidecar
```

Extending CI:

- Add coverage upload (e.g., Codecov) by appending a step after tests.
- Add SBOM generation with `pip install cyclonedx-bom && cyclonedx-py`.
- Push images on tagged releases by adding `push: true` and auth to the docker job.
- Add multi-arch builds (linux/amd64, linux/arm64) using buildx `platforms:` in release job.
- Add policy to require signed images before deployment (verify with `cosign verify`).
