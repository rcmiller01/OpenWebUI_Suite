# Environment Variable Setup Guide

## Quick Start

1. **Run the environment checker**:
   ```bash
   python3 scripts/env_check.py
   ```

2. **Or copy template and edit manually**:
   ```bash
   cp .env.template .env.prod
   # Edit .env.prod with your values
   ```

3. **Deploy with environment validation**:
   ```bash
   ./scripts/deploy_with_deps.sh    # Linux/Mac
   .\scripts\deploy_with_deps.ps1   # Windows
   ```

## Required Variables by Service

### 🔴 **Critical - Must Configure**

| Variable | Service | Description | Example |
|----------|---------|-------------|---------|
| `TANDOOR_URL` | Tandoor Sidecar | Tandoor Recipes URL | `http://tandoor:8080` |
| `TANDOOR_API_TOKEN` | Tandoor Sidecar | API token (preferred) | `your_token_here` |
| `OPENBB_PAT` | OpenBB Sidecar | Personal Access Token | `your_pat_here` |
| `OLLAMA_HOST` | Ollama Plugin | Ollama server URL | `http://localhost:11434` |

### 🟡 **Optional - Recommended**

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis for caching |
| `DEVICE` | `cuda` | PyTorch device (GPU) |
| `MAX_TOKENS` | `192` | VLM generation limit |

## Authentication Options

### Tandoor Recipes
Choose **ONE** method:

**Option 1: API Token (Recommended)**
```bash
TANDOOR_URL=http://tandoor:8080
TANDOOR_API_TOKEN=your_api_token_here
```

**Option 2: Username/Password**
```bash
TANDOOR_URL=http://tandoor:8080
TANDOOR_USERNAME=admin
TANDOOR_PASSWORD=your_password_here
```

### OpenBB Platform
```bash
OPENBB_PAT=your_personal_access_token
```

Get your PAT from: https://my.openbb.co/app/platform/pat

## GPU Configuration

For NVIDIA GPU acceleration:
```bash
DEVICE=cuda
TORCH_DTYPE=float16
FASTVLM_MODEL=apple/fastvlm-2.7b
```

For CPU-only:
```bash
DEVICE=cpu
TORCH_DTYPE=float32
```

For Apple Silicon:
```bash
DEVICE=mps
TORCH_DTYPE=float16
```

## Security Notes

⚠️ **Never commit .env.prod to git!**

The file is already in `.gitignore`, but be careful:
- Use strong passwords and tokens
- Rotate tokens regularly
- Use environment-specific configurations
- Consider using Docker secrets for production

## Validation

The deployment script automatically validates:
- ✅ Required variables are set
- ✅ URLs are properly formatted
- ✅ Ports are valid numbers
- ✅ Timeouts are positive integers

## Troubleshooting

### Missing Variables
```bash
❌ MISSING 🔴 REQUIRED TANDOOR_URL
```
**Fix**: Set the variable in `.env.prod`

### Invalid URLs
```bash
⚠️ Warning: TANDOOR_URL should start with http:// or https://
```
**Fix**: Use complete URL format

### Connection Issues
```bash
Failed to connect to Tandoor on startup
```
**Fix**: Verify the service is running and URL is correct

## Complete Example

```bash
# Core
REDIS_URL=redis://redis:6379

# Tandoor
TANDOOR_URL=http://tandoor:8080
TANDOOR_API_TOKEN=abcd1234...

# OpenBB
OPENBB_PAT=your_openbb_token

# GPU Setup
DEVICE=cuda
OLLAMA_HOST=http://gpu-server:11434

# File Storage
FILE_STORAGE_PATH=/data/files
MAX_FILE_BYTES=5242880

# Optional Telemetry
ENABLE_OTEL=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268
```
