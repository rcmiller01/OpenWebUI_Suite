#!/bin/bash
# Quick commands to complete your OpenWebUI Suite deployment
# Run these commands on your Linux production server

echo "🚀 OpenWebUI Suite - Quick Deployment Fix"
echo "========================================="

# Fix the service manager script syntax error
echo "1. Fixing service manager script..."
cd /opt/openwebui-suite
sed -i '371d' owui-service-manager.sh  # Remove the extra }

# Create missing services
echo "2. Creating missing services..."
sudo systemctl daemon-reload

# Missing services that need to be created
MISSING_DIRS=(
    "04-hidden-multi-expert-merger"
    "11-stt-tts-gateway" 
    "12-avatar-overlay"
    "14-telemetry-cache"
)

for dir in "${MISSING_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Creating systemd unit for $dir..."
        ./owui-service-manager.sh create-unit "$dir"
        
        # Start the service
        unit_name="owui-${dir}.service"
        sudo systemctl enable "$unit_name"
        sudo systemctl start "$unit_name"
    else
        echo "⚠️  Directory $dir not found"
    fi
done

# Fix the failing policy guardrails service
echo "3. Fixing policy-guardrails service..."
sudo systemctl stop owui-13-policy-guardrails.service 2>/dev/null || true
sleep 3
sudo systemctl start owui-13-policy-guardrails.service

# Show final status
echo "4. Final status check..."
echo "All OWUI services:"
systemctl list-units 'owui-*' --type=service

echo ""
echo "Health check summary:"
for port in {8100..8115}; do
    if curl -s -f "http://localhost:$port/healthz" >/dev/null 2>&1; then
        echo "✅ Service on port $port: Healthy"
    else
        echo "❌ Service on port $port: Not responding"
    fi
done

echo ""
echo "🎉 Deployment fix completed!"
echo "Expected: 16 services running"
echo "Run 'systemctl list-units owui-*' to see all services"
