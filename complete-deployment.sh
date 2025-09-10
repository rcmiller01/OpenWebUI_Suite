#!/bin/bash
# Complete OpenWebUI Suite Deployment Script
# Fixes missing services and deployment issues

set -e

echo "🚀 Completing OpenWebUI Suite Deployment"
echo "=========================================="

# Source directory
SUITE_DIR="/opt/openwebui-suite"
cd "$SUITE_DIR"

echo "📋 Current deployment status..."
systemctl list-units 'owui-*' --type=service --all

echo ""
echo "🔧 Creating missing service units..."

# Missing services to create
MISSING_SERVICES=(
    "04-hidden-multi-expert-merger"
    "11-stt-tts-gateway"
    "12-avatar-overlay"  
    "14-telemetry-cache"
)

for service in "${MISSING_SERVICES[@]}"; do
    echo "Creating service: $service"
    if [ -d "$service" ]; then
        ./owui-service-manager.sh create-unit "$service"
    else
        echo "⚠️  Directory $service not found - skipping"
    fi
done

echo ""
echo "🔄 Reloading systemd and starting missing services..."
sudo systemctl daemon-reload

for service in "${MISSING_SERVICES[@]}"; do
    unit_name="owui-${service}.service"
    if systemctl list-unit-files "$unit_name" >/dev/null 2>&1; then
        echo "Starting $unit_name..."
        sudo systemctl enable "$unit_name"
        sudo systemctl start "$unit_name"
        
        # Wait a moment and check status
        sleep 2
        if systemctl is-active "$unit_name" >/dev/null 2>&1; then
            echo "✅ $unit_name is active"
        else
            echo "❌ $unit_name failed to start"
            sudo systemctl status "$unit_name" --no-pager -l
        fi
    fi
done

echo ""
echo "🔧 Fixing policy-guardrails service..."
# Restart the failing service
sudo systemctl stop owui-13-policy-guardrails.service || true
sleep 2
sudo systemctl start owui-13-policy-guardrails.service

echo ""
echo "📊 Final deployment status..."
echo "Active services:"
systemctl list-units 'owui-*' --type=service --state=active

echo ""
echo "Failed services:"
systemctl list-units 'owui-*' --type=service --state=failed

echo ""
echo "🏥 Running health checks..."
for port in 8100 8101 8102 8103 8104 8105 8106 8107 8108 8109 8110 8111 8112 8113 8114 8115; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/healthz" | grep -q "200"; then
        echo "✅ Port $port: Healthy"
    else
        echo "❌ Port $port: Not responding"
    fi
done

echo ""
echo "🎉 Deployment completed!"
echo "Run './owui-service-manager.sh discover' for detailed status"
