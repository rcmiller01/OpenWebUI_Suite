#!/bin/bash
# Fix systemd units for services that have Python path issues

echo "🔧 Fixing Python path issues in systemd units..."

cd /opt/openwebui-suite

# Services that need fixing - they have start.py files and should use those instead of direct uvicorn
SERVICES_TO_FIX=(
    "01-intent-router"
    "02-memory-2.0"
    "03-feeling-engine"
    "04-hidden-multi-expert-merger"
    "05-drive-state"
    "09-proactive-daemon"
    "10-multimodal-router"
    "11-stt-tts-gateway"
    "12-avatar-overlay"
    "13-policy-guardrails"
    "14-telemetry-cache"
    "16-fastvlm-sidecar"
)

for service_dir in "${SERVICES_TO_FIX[@]}"; do
    unit_name="owui-${service_dir}.service"
    unit_file="/etc/systemd/system/${unit_name}"
    
    echo "Checking $service_dir..."
    
    # Check if start.py exists
    if [ -f "$service_dir/start.py" ]; then
        echo "  Found start.py - updating systemd unit to use it"
        
        # Stop the service first
        sudo systemctl stop "$unit_name"
        
        # Update the ExecStart line to use start.py instead of uvicorn
        sudo sed -i "s|ExecStart=.*uvicorn.*|ExecStart=/opt/openwebui-suite/.venv/bin/python3 /opt/openwebui-suite/${service_dir}/start.py|" "$unit_file"
        
        # Also update WorkingDirectory to the service directory
        sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=/opt/openwebui-suite/${service_dir}|" "$unit_file"
        
        echo "  ✅ Updated $unit_name"
    else
        echo "  ⚠️  No start.py found for $service_dir"
    fi
done

# Reload systemd and restart services
echo ""
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "🚀 Starting fixed services..."
for service_dir in "${SERVICES_TO_FIX[@]}"; do
    unit_name="owui-${service_dir}.service"
    
    if [ -f "$service_dir/start.py" ]; then
        echo "Starting $unit_name..."
        sudo systemctl start "$unit_name"
        sleep 2
        
        if systemctl is-active "$unit_name" >/dev/null 2>&1; then
            echo "  ✅ $unit_name is running"
        else
            echo "  ❌ $unit_name failed to start"
            echo "  Recent logs:"
            sudo journalctl -u "$unit_name" --no-pager -n 3 | sed 's/^/    /'
        fi
    fi
done

echo ""
echo "📊 Final status check..."
systemctl list-units 'owui-*' --type=service --no-pager

echo ""
echo "🏥 Health check..."
for port in {8100..8115}; do
    if curl -s -f "http://localhost:$port/healthz" >/dev/null 2>&1; then
        echo "✅ Port $port: Healthy"
    else
        echo "❌ Port $port: Not responding"
    fi
done

echo ""
echo "✅ Python path fix completed!"
