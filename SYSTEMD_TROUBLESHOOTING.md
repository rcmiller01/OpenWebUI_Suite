# Systemd Unit Troubleshooting Guide

## Issue: Service Unit Creation Failures

If you encounter errors like "owui-06-byof-tool-hub.service not found" after apparently successful unit creation, use these troubleshooting steps.

### Enhanced Service Manager Features

The `owui-service-manager.sh` script now includes robust unit validation and fixing:

```bash
# Verify all systemd units are valid and fix any issues
./owui-service-manager.sh verify

# This will:
# 1. Check if each unit file exists
# 2. Validate unit file syntax with systemd-analyze
# 3. Recreate any missing or invalid units
# 4. Show a summary table of all unit statuses
```

### Common Systemd Issues and Solutions

#### 1. Unit File Not Found
**Symptoms:** `systemctl status service` shows "Unit not found"
**Cause:** Unit file missing or systemd hasn't reloaded
**Solution:**
```bash
# Check if unit file exists
ls -la /etc/systemd/system/owui-*.service

# Force systemd reload
sudo systemctl daemon-reload

# Recreate missing units
./owui-service-manager.sh verify
```

#### 2. Invalid Unit File Syntax
**Symptoms:** Unit file exists but systemd rejects it
**Cause:** Syntax errors in unit file
**Solution:**
```bash
# Check specific unit syntax
sudo systemd-analyze verify /etc/systemd/system/owui-06-byof-tool-hub.service

# Auto-fix with verify command
./owui-service-manager.sh verify
```

#### 3. Service Fails to Start
**Symptoms:** Unit exists but service won't start
**Debugging:**
```bash
# Check detailed status
sudo systemctl status owui-06-byof-tool-hub.service

# Check recent logs
sudo journalctl -u owui-06-byof-tool-hub.service -n 50

# Check service-specific logs
./owui-service-manager.sh logs 06-byof-tool-hub
```

### Validation Steps

The improved `create_service_unit` function now includes:

1. **Pre-creation validation:**
   - Check if service directory exists
   - Verify start script is present
   - Confirm service configuration

2. **Post-creation validation:**
   - Syntax check with `systemd-analyze verify`
   - Systemd recognition test
   - Unit file permissions check

3. **Error reporting:**
   - Detailed error messages for each failure type
   - Suggestions for manual fixes
   - Log file locations for debugging

### Manual Unit Creation (Last Resort)

If automatic creation fails, create units manually:

```bash
# Example for 06-byof-tool-hub
sudo tee /etc/systemd/system/owui-06-byof-tool-hub.service << 'EOF'
[Unit]
Description=OpenWebUI BYOF Tool Hub
After=network.target
Wants=network.target

[Service]
Type=simple
User=owui
Group=owui
WorkingDirectory=/opt/openwebui-suite/06-byof-tool-hub
ExecStart=/opt/openwebui-suite/06-byof-tool-hub/start.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/openwebui-suite/06-byof-tool-hub
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload and test
sudo systemctl daemon-reload
sudo systemd-analyze verify owui-06-byof-tool-hub.service
sudo systemctl enable owui-06-byof-tool-hub.service
```

### Production Deployment Checklist

1. **Run verification before deployment:**
   ```bash
   ./owui-service-manager.sh verify
   ```

2. **Check all units are valid:**
   ```bash
   sudo systemd-analyze verify /etc/systemd/system/owui-*.service
   ```

3. **Test service startup:**
   ```bash
   ./owui-service-manager.sh bring-up
   ```

4. **Monitor health:**
   ```bash
   ./owui-service-manager.sh health
   ```

### Error Log Locations

- **Systemd journal:** `sudo journalctl -u <service-name>`
- **Service logs:** `./owui-service-manager.sh logs <service>`
- **Script errors:** Check terminal output from service manager

### Support Information

If issues persist:
1. Run `./owui-service-manager.sh verify` and share output
2. Check `sudo journalctl -u <failing-service> -n 100`
3. Verify file permissions: `ls -la /etc/systemd/system/owui-*.service`
4. Test manual service start: `sudo systemctl start <service-name>`

The enhanced service manager should resolve most systemd unit issues automatically.
</content>
</invoke>
