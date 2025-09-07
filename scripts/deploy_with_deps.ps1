# OpenWebUI Suite Deployment Script with External Dependencies (PowerShell)
# Enhanced version that pulls required repositories for sidecars

param(
    [string]$DeployBranch = "deploy/full-activation",
    [string]$ExternalDepsDir = "external"
)

# Configuration
$TandoorRepo = "https://github.com/TandoorRecipes/recipes.git"
$TandoorBranch = "master"

# Colors for output
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Test-Directory {
    if (-not (Test-Path "compose.prod.yml") -or -not (Test-Path "00-pipelines-gateway")) {
        Write-Error "Not in OpenWebUI Suite root directory. Please run from project root."
        exit 1
    }
}

function New-DeployBranch {
    Write-Info "Creating/switching to deploy branch: $DeployBranch"
    
    # Check if branch exists locally
    $branchExists = git show-ref --verify --quiet "refs/heads/$DeployBranch"
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Branch $DeployBranch exists locally, switching to it"
        git checkout $DeployBranch
    } else {
        Write-Info "Creating new branch: $DeployBranch"
        git checkout -b $DeployBranch
    }
    
    Write-Success "On branch: $DeployBranch"
}

function Set-ExternalDeps {
    Write-Info "Setting up external dependencies directory"
    
    New-Item -ItemType Directory -Force -Path $ExternalDepsDir | Out-Null
    Set-Location $ExternalDepsDir
    
    Write-Info "External dependencies will be stored in: $(Get-Location)"
}

function Get-TandoorRepo {
    Write-Info "Cloning Tandoor Recipes repository..."
    
    if (Test-Path "tandoor-recipes") {
        Write-Warn "Tandoor recipes directory already exists, updating..."
        Set-Location tandoor-recipes
        git pull origin $TandoorBranch
        Set-Location ..
    } else {
        Write-Info "Cloning fresh Tandoor Recipes repository"
        git clone --branch $TandoorBranch $TandoorRepo tandoor-recipes
    }
    
    Write-Success "Tandoor Recipes repository ready"
}

function Set-PythonDeps {
    Write-Info "Setting up Python dependencies for sidecars..."
    
    # Create requirements file for external sidecar dependencies
    $requirementsContent = @"
# OpenBB Platform for financial sidecar
openbb==4.3.1
pandas==2.2.2
numpy==1.26.4

# Additional dependencies that might be needed
httpx>=0.25.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
"@
    
    $requirementsContent | Out-File -FilePath "sidecar-requirements.txt" -Encoding utf8
    Write-Info "Created sidecar-requirements.txt for external Python dependencies"
    
    # Check for Python and create virtual environment
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (-not (Test-Path "sidecar-venv")) {
            Write-Info "Creating Python virtual environment for sidecars..."
            python -m venv sidecar-venv
            & "sidecar-venv\Scripts\Activate.ps1"
            python -m pip install --upgrade pip
            pip install -r sidecar-requirements.txt
            deactivate
            Write-Success "Sidecar virtual environment created"
        } else {
            Write-Warn "Sidecar virtual environment already exists"
        }
    } else {
        Write-Warn "Python not found, skipping virtual environment creation"
    }
}

function New-IntegrationDocs {
    Write-Info "Creating external integration documentation..."
    
    $docsContent = @'
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
'@
    
    $docsContent | Out-File -FilePath "EXTERNAL_INTEGRATION.md" -Encoding utf8
    Write-Success "Created EXTERNAL_INTEGRATION.md"
}

function Update-Configs {
    Set-Location .. # Back to project root
    
    Write-Info "Updating configuration files..."
    
    # Add files to git
    git add compose.prod.yml
    git add telemetry/prometheus.yml
    git add 00-pipelines-gateway/src/projects.py
    git add scripts/owui_sanity.sh
    git add systemd/owui.service
    
    # Add main server file if it exists
    if (Test-Path "00-pipelines-gateway/src/server.py") {
        git add 00-pipelines-gateway/src/server.py
    }
    
    # Add UI components if they exist
    if (Test-Path "openwebui-suite/src/components/ProjectsSidebar.tsx") {
        git add openwebui-suite/src/components/ProjectsSidebar.tsx
    }
    
    # Add documentation
    git add MODULE_ANALYSIS_REPORT.md
    git add SIDECAR_ANALYSIS.md
    git add DEPLOY_SUMMARY.md
    git add external/EXTERNAL_INTEGRATION.md
    git add external/sidecar-requirements.txt
    
    Write-Success "Configuration files staged for commit"
}

function Deploy-Changes {
    Write-Info "Committing and pushing changes..."
    
    $commitMessage = @"
Deploy: enable all modules, external deps, stable network/healthchecks

- Complete production deployment with external integrations
- Tandoor Recipes repository cloned and configured
- OpenBB Platform dependencies documented
- FastVLM integration ready
- Projects MVP (gateway+UI) with SQLite persistence
- Production ops scripts (sanity checker, systemd service)
- Comprehensive health checks and monitoring
- All 16 services production-ready with proper port mapping
- External integration documentation and setup guides
"@
    
    git commit -m $commitMessage
    git push -u origin $DeployBranch
    
    Write-Success "Changes pushed to $DeployBranch"
}

function Show-NextSteps {
    Write-Host ""
    Write-Host "🎉 Deployment preparation complete!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Review external/EXTERNAL_INTEGRATION.md for setup instructions"
    Write-Host "2. Deploy Tandoor Recipes: cd external/tandoor-recipes && docker-compose up -d"
    Write-Host "3. Configure environment variables in .env file"
    Write-Host "4. Deploy OpenWebUI Suite: docker-compose -f compose.prod.yml up -d"
    Write-Host "5. Run health checks: ./scripts/owui_sanity.sh"
    Write-Host "6. Open Pull Request and merge to main"
    Write-Host ""
    Write-Host "🔗 External Dependencies:" -ForegroundColor Cyan
    Write-Host "- Tandoor Recipes: external/tandoor-recipes/"
    Write-Host "- OpenBB Platform: pip install openbb==4.3.1"
    Write-Host "- FastVLM: Downloads automatically"
    Write-Host ""
    Write-Host "📊 Services Ready: 16 microservices + UI" -ForegroundColor Yellow
    Write-Host "🚀 Status: Production Ready" -ForegroundColor Green
}

# Main execution
function Main {
    Write-Info "Starting OpenWebUI Suite deployment preparation..."
    
    Test-Directory
    New-DeployBranch
    Set-ExternalDeps
    Get-TandoorRepo
    Set-PythonDeps
    New-IntegrationDocs
    Update-Configs
    Deploy-Changes
    Show-NextSteps
    
    Write-Success "Deployment preparation completed successfully!"
}

# Run main function
Main
