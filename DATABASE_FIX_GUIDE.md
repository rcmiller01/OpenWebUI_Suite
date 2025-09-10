# SQLite Database Fix Deployment Guide

## Problem
The `00-pipelines-gateway` service was failing to start with the error:
```
sqlite3.OperationalError: unable to open database file
```

This occurred because the database path `/data/gateway.db` was trying to write to a directory that didn't exist and had no proper permissions.

## Solution Applied

### 1. Code Changes
- **projects.py**: Updated to create database directory if it doesn't exist
- **Dockerfile**: Added `/app/data` directory creation with proper permissions
- **docker-compose.yml**: Added persistent volume for database storage

### 2. Database Path
- **Development**: `./00-pipelines-gateway/data/gateway.db`  
- **Production**: `/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db`
- **Container**: `/app/data/gateway.db` (with volume mount)

## Deployment Steps

### For Production Server (Linux)
1. Copy the fix script to the server:
   ```bash
   scp fix-gateway-db.sh user@server:/opt/openwebui-suite/
   ```

2. Run the fix script:
   ```bash
   cd /opt/openwebui-suite
   chmod +x fix-gateway-db.sh
   ./fix-gateway-db.sh
   ```

3. Verify the service is running:
   ```bash
   sudo systemctl status owui-00-pipelines-gateway.service
   curl http://localhost:8088/healthz
   ```

### For Docker Deployment
1. Rebuild the gateway container:
   ```bash
   docker-compose build 00-pipelines-gateway
   ```

2. Start with persistent volume:
   ```bash
   docker-compose up -d 00-pipelines-gateway
   ```

3. Verify health:
   ```bash
   docker-compose logs 00-pipelines-gateway
   curl http://localhost:8088/healthz
   ```

### For Local Development
1. Run the PowerShell fix script:
   ```powershell
   .\fix-gateway-db.ps1
   ```

2. Start the development server:
   ```bash
   cd 00-pipelines-gateway
   python -m uvicorn src.server:app --host 0.0.0.0 --port 8088 --reload
   ```

## Environment Variables

Add to your `.env` file:
```bash
# Gateway Database Configuration
GATEWAY_DB=/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db
```

For containers, the path will be automatically set to `/app/data/gateway.db`.

## Verification

After deployment, verify the fix:

1. **Service Status**: 
   ```bash
   sudo systemctl status owui-00-pipelines-gateway.service
   ```

2. **Health Check**: 
   ```bash
   curl http://localhost:8088/healthz
   ```

3. **Database Creation**: 
   ```bash
   ls -la /opt/openwebui-suite/00-pipelines-gateway/data/
   ```

4. **Service Logs**: 
   ```bash
   sudo journalctl -u owui-00-pipelines-gateway.service -f
   ```

The database file `gateway.db` should be created automatically when the service starts.
