# OpenWebUI Suite Deployment Scripts

This directory contains scripts for deploying and managing the OpenWebUI Suite.

## Scripts Overview

### 🚀 Deployment Scripts

#### `deploy_with_deps.sh` / `deploy_with_deps.ps1`
**Enhanced deployment scripts that automatically pull external dependencies**

**Features:**
- Creates/switches to deploy branch
- Clones required external repositories (Tandoor Recipes)
- Sets up Python dependencies for sidecars  
- Creates integration documentation
- Commits and pushes all changes
- Provides comprehensive next steps

**Usage:**
```bash
# Linux/Mac
./scripts/deploy_with_deps.sh

# Windows PowerShell  
.\scripts\deploy_with_deps.ps1
```

**What it does:**
1. ✅ Creates `deploy/full-activation` branch
2. ✅ Clones Tandoor Recipes to `external/tandoor-recipes/`
3. ✅ Creates `external/sidecar-requirements.txt` for Python deps
4. ✅ Sets up virtual environment with OpenBB Platform
5. ✅ Generates `external/EXTERNAL_INTEGRATION.md` documentation
6. ✅ Stages all deployment files
7. ✅ Commits with comprehensive message
8. ✅ Pushes to remote repository

### 🏥 Health Check Scripts

#### `owui_sanity.sh`
**Production health check and validation script**

**Features:**
- Docker Compose configuration validation
- Network connectivity testing
- Service health endpoint verification  
- DNS resolution checks
- Service dependency validation

**Usage:**
```bash
./scripts/owui_sanity.sh
```

**Services Checked:**
- Gateway (8000) - Projects backend and routing
- Intent Router (8101) - ML classification
- Memory (8102) - Persistent memory
- Feeling Engine (8103) - Emotion analysis
- Policy Guardrails (8113) - Content moderation
- Telemetry Cache (8114) - Observability

### ⚙️ System Integration

#### `systemd/owui.service`
**SystemD service for auto-start capability**

**Installation:**
```bash
sudo cp systemd/owui.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable owui.service
sudo systemctl start owui.service
```

## External Dependencies

### Automatically Pulled:
- **Tandoor Recipes**: Recipe management system
  - Repository: `https://github.com/TandoorRecipes/recipes.git`
  - Location: `external/tandoor-recipes/`
  - Purpose: Backend for 07-tandoor-sidecar

### Automatically Configured:
- **OpenBB Platform**: Financial data integration
  - Package: `openbb==4.3.1`
  - Installation: Via pip in virtual environment
  - Purpose: Backend for 08-openbb-sidecar

- **Apple FastVLM**: Local vision model
  - Model: `apple/fastvlm-2.7b`
  - Source: Hugging Face (auto-download)
  - Purpose: 16-fastvlm-sidecar processing

## Environment Variables

The deployment scripts help configure these required variables:

```bash
# External Service Integrations
TANDOOR_URL=http://localhost:8080
TANDOOR_API_TOKEN=your_tandoor_token_here
OPENBB_PAT=your_openbb_personal_access_token
OPENROUTER_API_KEY=your_openrouter_api_key

# Internal Configuration  
GATEWAY_DB=/data/gateway.db
ENABLE_PROJECTS=true
REDIS_URL=redis://localhost:6379

# Optional Model Configuration
FASTVLM_MODEL=apple/fastvlm-2.7b
STT_MODEL_SIZE=base
DEVICE=cuda
```

## Troubleshooting

### Common Issues:

1. **Git repository not found**
   - Ensure you're in the OpenWebUI Suite root directory
   - Check that `.git` directory exists

2. **External repository clone fails**
   - Check internet connectivity
   - Verify GitHub access permissions
   - Try manual clone: `git clone https://github.com/TandoorRecipes/recipes.git`

3. **Python dependencies fail**
   - Ensure Python 3.8+ is installed
   - Check pip version: `pip --version`
   - Try manual install: `pip install openbb==4.3.1`

4. **Health checks fail**
   - Verify Docker and Docker Compose are running
   - Check service logs: `docker-compose logs <service-name>`
   - Ensure all required ports are available

### Support:
- Check deployment documentation: `DEPLOY_SUMMARY.md`
- Review integration guide: `external/EXTERNAL_INTEGRATION.md`
- Validate service architecture: `MODULE_ANALYSIS_REPORT.md`

## Security Considerations

- ⚠️ **API Tokens**: Never commit API tokens to version control
- ⚠️ **Environment Files**: Add `.env` to `.gitignore` 
- ⚠️ **External Services**: Ensure external services are properly secured
- ⚠️ **Network Access**: Configure firewall rules for exposed ports
- ⚠️ **SSL/TLS**: Use HTTPS in production deployments

## Monitoring

After deployment, monitor via:
- **Health Endpoints**: All services expose `/healthz`
- **Prometheus Metrics**: `http://localhost:8114/metrics`
- **Service Logs**: `docker-compose logs -f`
- **System Health**: `./scripts/owui_sanity.sh`
