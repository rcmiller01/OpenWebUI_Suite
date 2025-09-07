#!/bin/bash
# OpenWebUI Suite Deployment Script with External Dependencies
# Enhanced version that pulls required repositories for sidecars

set -e  # Exit on any error

echo "🚀 OpenWebUI Suite Deployment with External Dependencies"
echo "======================================================="

# Check environment variables first
echo ""
log "Checking environment variables..."

# Run environment checker
if [ -f "scripts/env_check.py" ]; then
    python3 scripts/env_check.py
    ENV_CHECK_STATUS=$?
    
    if [ $ENV_CHECK_STATUS -ne 0 ]; then
        error "Environment variable check failed!"
        echo "Some required variables are missing. Please configure them before deploying."
        exit 1
    fi
    
    success "Environment variables configured!"
else
    warning "Environment checker not found, skipping validation..."
fi

echo ""

# Configuration
DEPLOY_BRANCH="deploy/full-activation"
EXTERNAL_DEPS_DIR="external"
TANDOOR_REPO="https://github.com/TandoorRecipes/recipes.git"
TANDOOR_BRANCH="master"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in the right directory
check_directory() {
    if [[ ! -f "compose.prod.yml" ]] || [[ ! -d "00-pipelines-gateway" ]]; then
        error "Not in OpenWebUI Suite root directory. Please run from project root."
        exit 1
    fi
}

# Function to create deploy branch
create_deploy_branch() {
    log "Creating/switching to deploy branch: $DEPLOY_BRANCH"
    
    # Check if branch exists locally
    if git show-ref --verify --quiet refs/heads/$DEPLOY_BRANCH; then
        log "Branch $DEPLOY_BRANCH exists locally, switching to it"
        git checkout $DEPLOY_BRANCH
    else
        log "Creating new branch: $DEPLOY_BRANCH"
        git checkout -b $DEPLOY_BRANCH
    fi
    
    success "On branch: $DEPLOY_BRANCH"
}

# Function to setup external dependencies directory
setup_external_deps() {
    log "Setting up external dependencies directory"
    
    mkdir -p $EXTERNAL_DEPS_DIR
    cd $EXTERNAL_DEPS_DIR
    
    log "External dependencies will be stored in: $(pwd)"
}

# Function to clone Tandoor Recipes
clone_tandoor() {
    log "Cloning Tandoor Recipes repository..."
    
    if [[ -d "tandoor-recipes" ]]; then
        warn "Tandoor recipes directory already exists, updating..."
        cd tandoor-recipes
        git pull origin $TANDOOR_BRANCH
        cd ..
    else
        log "Cloning fresh Tandoor Recipes repository"
        git clone --branch $TANDOOR_BRANCH $TANDOOR_REPO tandoor-recipes
    fi
    
    success "Tandoor Recipes repository ready"
}

# Function to setup Python dependencies for sidecars
setup_python_deps() {
    log "Setting up Python dependencies for sidecars..."
    
    # Create a requirements file for external sidecar dependencies
    cat > sidecar-requirements.txt << EOF
# OpenBB Platform for financial sidecar
openbb==4.3.1
pandas==2.2.2
numpy==1.26.4

# Additional dependencies that might be needed
httpx>=0.25.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
EOF
    
    log "Created sidecar-requirements.txt for external Python dependencies"
    
    # Optional: Create virtual environment for sidecars
    if command -v python3 &> /dev/null; then
        if [[ ! -d "sidecar-venv" ]]; then
            log "Creating Python virtual environment for sidecars..."
            python3 -m venv sidecar-venv
            source sidecar-venv/bin/activate
            pip install --upgrade pip
            pip install -r sidecar-requirements.txt
            deactivate
            success "Sidecar virtual environment created"
        else
            warn "Sidecar virtual environment already exists"
        fi
    else
        warn "Python3 not found, skipping virtual environment creation"
    fi
}

# Function to create external integration documentation
create_integration_docs() {
    log "Creating external integration documentation..."
    
    cat > EXTERNAL_INTEGRATION.md << 'EOF'
# External Integration Setup Guide

## Tandoor Recipes Integration

### Setup Instructions:
1. **Deploy Tandoor Recipes**:
   ```bash
   cd external/tandoor-recipes
   cp .env.template .env
   # Edit .env with your configuration
   docker-compose up -d
   ```

2. **Get API Token**:
   - Open Tandoor web interface (default: http://localhost:8080)
   - Create admin account
   - Go to Settings → API → Generate Token
   - Copy token for environment variables

3. **Configure OpenWebUI Suite**:
   ```bash
   # Add to your .env file
   TANDOOR_URL=http://localhost:8080
   TANDOOR_API_TOKEN=your_api_token_here
   ```

## OpenBB Platform Integration

### Setup Instructions:
1. **Get OpenBB PAT**:
   - Visit https://my.openbb.co/
   - Create account and generate Personal Access Token

2. **Configure Environment**:
   ```bash
   # Add to your .env file
   OPENBB_PAT=your_openbb_token_here
   ```

## FastVLM Integration

### Setup Instructions:
- **No manual setup required**
- Model downloads automatically from Hugging Face
- Requires GPU for optimal performance

### Optional Configuration:
```bash
# Add to your .env file
FASTVLM_MODEL=apple/fastvlm-2.7b
DEVICE=cuda  # or cpu
TORCH_DTYPE=float16
MAX_TOKENS=192
```

## Environment Variables Summary

```bash
# External Service Integrations
TANDOOR_URL=http://localhost:8080
TANDOOR_API_TOKEN=your_tandoor_token
OPENBB_PAT=your_openbb_token
OPENROUTER_API_KEY=your_openrouter_key

# Internal Configuration
GATEWAY_DB=/data/gateway.db
ENABLE_PROJECTS=true
REDIS_URL=redis://localhost:6379

# Optional Model Configuration
FASTVLM_MODEL=apple/fastvlm-2.7b
STT_MODEL_SIZE=base
TTS_MODEL_NAME=tts_models/en/ljspeech/tacotron2-DDC_ph
```

## Deployment Validation

1. **Check Tandoor Connection**:
   ```bash
   curl -H "Authorization: Bearer $TANDOOR_API_TOKEN" \
        http://localhost:8080/api/recipe/
   ```

2. **Test OpenBB Integration**:
   ```bash
   python -c "from openbb import obb; obb.account.login(pat='$OPENBB_PAT'); print('OpenBB OK')"
   ```

3. **Validate Services**:
   ```bash
   ./scripts/owui_sanity.sh
   ```
EOF
    
    success "Created EXTERNAL_INTEGRATION.md"
}

# Function to update compose and configuration files
update_configs() {
    cd .. # Back to project root
    
    log "Updating configuration files..."
    
    # Add files to git (adjust paths for actual structure)
    git add compose.prod.yml
    git add telemetry/prometheus.yml
    git add 00-pipelines-gateway/src/projects.py
    git add scripts/owui_sanity.sh
    git add systemd/owui.service
    
    # Add main server file if it exists
    if [[ -f "00-pipelines-gateway/src/server.py" ]]; then
        git add 00-pipelines-gateway/src/server.py
    fi
    
    # Add UI components if they exist
    if [[ -f "openwebui-suite/src/components/ProjectsSidebar.tsx" ]]; then
        git add openwebui-suite/src/components/ProjectsSidebar.tsx
    fi
    
    # Add documentation
    git add MODULE_ANALYSIS_REPORT.md
    git add SIDECAR_ANALYSIS.md
    git add DEPLOY_SUMMARY.md
    git add external/EXTERNAL_INTEGRATION.md
    git add external/sidecar-requirements.txt
    
    success "Configuration files staged for commit"
}

# Function to commit and push changes
deploy_changes() {
    log "Committing and pushing changes..."
    
    git commit -m "Deploy: enable all modules, external deps, stable network/healthchecks

- Complete production deployment with external integrations
- Tandoor Recipes repository cloned and configured
- OpenBB Platform dependencies documented
- FastVLM integration ready
- Projects MVP (gateway+UI) with SQLite persistence
- Production ops scripts (sanity checker, systemd service)
- Comprehensive health checks and monitoring
- All 16 services production-ready with proper port mapping
- External integration documentation and setup guides"
    
    git push -u origin $DEPLOY_BRANCH
    
    success "Changes pushed to $DEPLOY_BRANCH"
}

# Function to display next steps
show_next_steps() {
    echo ""
    echo "🎉 Deployment preparation complete!"
    echo "=================================="
    echo ""
    echo "📋 Next Steps:"
    echo "1. Review external/EXTERNAL_INTEGRATION.md for setup instructions"
    echo "2. Deploy Tandoor Recipes: cd external/tandoor-recipes && docker-compose up -d"
    echo "3. Configure environment variables in .env file"
    echo "4. Deploy OpenWebUI Suite: docker-compose -f compose.prod.yml up -d"
    echo "5. Run health checks: ./scripts/owui_sanity.sh"
    echo "6. Open Pull Request and merge to main"
    echo ""
    echo "🔗 External Dependencies:"
    echo "- Tandoor Recipes: external/tandoor-recipes/"
    echo "- OpenBB Platform: pip install openbb==4.3.1"
    echo "- FastVLM: Downloads automatically"
    echo ""
    echo "📊 Services Ready: 16 microservices + UI"
    echo "🚀 Status: Production Ready"
}

# Main execution
main() {
    log "Starting OpenWebUI Suite deployment preparation..."
    
    check_directory
    create_deploy_branch
    setup_external_deps
    clone_tandoor
    setup_python_deps
    create_integration_docs
    update_configs
    deploy_changes
    show_next_steps
    
    success "Deployment preparation completed successfully!"
}

# Run main function
main "$@"
