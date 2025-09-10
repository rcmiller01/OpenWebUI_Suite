# Service Manager v1.4 - Enhanced Debugging & Module Detection

## Recent Improvements

### Issue Resolved: 06-byof-tool-hub Import Error

**Problem**: Service failing with "Could not import module 'src.server'" because:
- Service has `src/app.py` not `src/server.py`
- Service has a `start.py` that properly configures uvicorn
- Detection logic was incorrectly categorizing it as "fastapi" type

**Solution**: Enhanced service type detection and FastAPI module path resolution.

### Enhanced Service Type Detection

```bash
# New improved detection logic:
detect_service_type() {
    if [ -f "package.json" ]; then
        echo "nodejs"
    elif [ -f "start.py" ]; then
        echo "python"     # Prefer start.py when available
    elif [ -f "src/server.py" ]; then
        echo "fastapi"    # Only for src/server.py specifically
    elif [ -f "src/worker.py" ]; then
        echo "worker"
    elif [ -f "src/app.py" ] && [ ! -f "start.py" ]; then
        echo "fastapi"    # src/app.py only if no start.py
    elif [ -f "start.sh" ]; then
        echo "shell"
    else
        echo "unknown"
    fi
}
```

### Smart FastAPI Module Detection

The `create_fastapi_unit` function now automatically detects the correct module path:

- **src/server.py exists**: Uses `src.server:app`  
- **src/app.py exists (no server.py)**: Uses `src.app:app`
- **Fallback**: Uses `src.server:app`

### New `info` Command

Diagnose service structure and configuration issues:

```bash
./owui-service-manager.sh info 06-byof-tool-hub
```

Output example:
```
🔍 Service Information: 06-byof-tool-hub
📁 Path: /opt/openwebui-suite/06-byof-tool-hub
🏷️  Type: python

📋 File Structure:
  ✅ start.py (Python entry point)
    → Contains uvicorn (FastAPI)
  ✅ src/app.py (FastAPI app)

🔧 Current Systemd Unit:
ExecStart line:
ExecStart=/usr/bin/python3 start.py
```

### Service Classification Results

After improvements, services should be classified as:

**Python Type (uses start.py):**
- 06-byof-tool-hub (has start.py with uvicorn config)

**FastAPI Type (direct uvicorn):**
- Services with src/server.py only
- Services with src/app.py but no start.py

**Node.js Type:**
- 12-avatar-overlay (has package.json)

**Worker Type:**
- 09-proactive-daemon (has src/worker.py)

### Troubleshooting Workflow

1. **Check service structure**:
   ```bash
   ./owui-service-manager.sh info <service-name>
   ```

2. **Verify/fix units**:
   ```bash
   ./owui-service-manager.sh verify
   ```

3. **Recreate specific unit**:
   ```bash
   ./owui-service-manager.sh create-unit <service-name>
   ```

4. **Check logs**:
   ```bash
   ./owui-service-manager.sh logs <service-name>
   ```

### Production Deployment Steps

For the current issue, run on the production server:

```bash
# 1. Pull latest code with enhanced service manager
git pull origin main

# 2. Check the problematic service structure
./owui-service-manager.sh info 06-byof-tool-hub

# 3. Recreate the unit with correct detection
./owui-service-manager.sh create-unit 06-byof-tool-hub

# 4. Start the service
sudo systemctl start owui-06-byof-tool-hub.service

# 5. Verify it's working
./owui-service-manager.sh health 06-byof-tool-hub
```

The enhanced service manager should now correctly detect that `06-byof-tool-hub` is a "python" type service and create a unit that runs `start.py` directly, rather than trying to use uvicorn with `src.server:app`.
</content>
</invoke>
