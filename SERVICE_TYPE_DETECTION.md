# Service Type Detection Update

## Issue Resolved

The `12-avatar-overlay` service was failing with "No module named 'src'" because it's a Node.js/Vite service, but the systemd unit was trying to run it as a Python service.

## Solution Implemented

Enhanced the `owui-service-manager.sh` with automatic service type detection:

### Service Type Detection Logic

```bash
detect_service_type() {
    if [ -f "package.json" ]; then
        echo "nodejs"      # Node.js/npm services
    elif [ -f "src/server.py" ] || [ -f "src/app.py" ]; then
        echo "fastapi"     # FastAPI services
    elif [ -f "src/worker.py" ]; then
        echo "worker"      # Background worker services
    elif [ -f "start.py" ]; then
        echo "python"      # Direct Python services
    elif [ -f "start.sh" ]; then
        echo "shell"       # Shell script services
    else
        echo "unknown"     # Fallback
    fi
}
```

### Service Types and Unit Templates

1. **nodejs**: For services with `package.json` (12-avatar-overlay)
   - Uses npm install and start.sh
   - Sets NODE_ENV=production
   - Default port 5173

2. **fastapi**: For services with `src/server.py` (most HTTP services)
   - Uses uvicorn with FastAPI
   - Configurable ports from SERVICES array
   - Database environment variables

3. **worker**: For services with `src/worker.py` (background tasks)
   - Direct Python execution
   - No port binding
   - Continuous running

4. **python**: For services with `start.py` (simple Python services)
   - Direct Python script execution
   - Basic environment setup

5. **shell**: For services with `start.sh` (custom shell services)
   - Bash script execution
   - Generic environment

### Enhanced Features

- **Automatic type detection**: No manual configuration needed
- **Service-specific units**: Proper ExecStart commands for each type
- **Validation**: Checks for required files before unit creation
- **Error handling**: Clear messages when files are missing

### Usage

The enhanced service manager automatically detects service types:

```bash
# This now works for all service types automatically
./owui-service-manager.sh verify

# Example output:
# ✅ Detected service type: nodejs for 12-avatar-overlay
# ✅ Detected service type: fastapi for 00-pipelines-gateway
# ✅ Detected service type: worker for 09-proactive-daemon
```

### Services by Type

**Node.js Services:**
- 12-avatar-overlay (frontend/web interface)

**FastAPI Services:**
- 00-pipelines-gateway
- 01-intent-router  
- 02-memory-2.0
- 03-feeling-engine
- 04-hidden-multi-expert-merger
- 05-drive-state
- 06-byof-tool-hub
- 07-tandoor-sidecar
- 08-openbb-sidecar
- 10-multimodal-router
- 11-stt-tts-gateway
- 13-policy-guardrails
- 14-telemetry-cache
- 16-fastvlm-sidecar

**Worker Services:**
- 09-proactive-daemon

This should resolve the Node.js service startup issues and make the deployment more robust across different service types.
</content>
</invoke>
