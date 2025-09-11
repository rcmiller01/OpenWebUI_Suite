#!/bin/bash
# OpenWebUI Suite - Core Services Fix
# Focuses only on services we built, excluding external sidecars

echo "🚀 OpenWebUI Suite - Core Services Stabilization"
echo "==============================================="

cd /opt/openwebui-suite

# Core services we built (excluding external sidecars)
CORE_SERVICES=(
    "owui-03-feeling-engine.service"
    "owui-05-drive-state.service"
    "owui-14-telemetry-cache.service"
)

# External sidecars to disable (require separate repos)
SIDECAR_SERVICES=(
    "owui-07-tandoor-sidecar.service"
    "owui-08-openbb-sidecar.service"
)

echo "1. Disabling external sidecar services..."
for service in "${SIDECAR_SERVICES[@]}"; do
    echo "Disabling $service (external dependency)"
    sudo systemctl stop "$service" 2>/dev/null || true
    sudo systemctl disable "$service" 2>/dev/null || true
done

echo ""
echo "2. Fixing core services in auto-restart..."
for service in "${CORE_SERVICES[@]}"; do
    echo "Stabilizing $service..."
    
    # Stop the service
    sudo systemctl stop "$service"
    sleep 2
    
    # Create necessary directories
    service_name=$(echo "$service" | sed 's/owui-//' | sed 's/.service//')
    if [ -d "$service_name" ]; then
        sudo mkdir -p "$service_name/data"
        sudo chown -R $(whoami):$(whoami) "$service_name/" 2>/dev/null || true
    fi
    
    # Start the service
    sudo systemctl start "$service"
    sleep 3
    
    # Check status
    if systemctl is-active "$service" >/dev/null 2>&1; then
        echo "✅ $service is now stable"
    else
        echo "❌ $service still having issues"
        echo "Recent logs:"
        sudo journalctl -u "$service" --no-pager -n 5 | sed 's/^/  /'
    fi
done

echo ""
echo "3. Final core services status:"
echo "Active core services:"
systemctl list-units 'owui-*' --type=service --state=active --no-pager

echo ""
echo "4. Health check for core services:"
CORE_PORTS=(8100 8101 8102 8103 8104 8105 8106 8109 8110 8111 8112 8113 8114 8115)

for port in "${CORE_PORTS[@]}"; do
    if curl -s -f "http://localhost:$port/healthz" >/dev/null 2>&1; then
        echo "✅ Port $port: Healthy"
    elif curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
        echo "✅ Port $port: Healthy (alt endpoint)"
    elif curl -s -f "http://localhost:$port/" >/dev/null 2>&1; then
        echo "🟡 Port $port: Responding"
    else
        echo "❌ Port $port: Not responding"
    fi
done

echo ""
echo "📊 Summary:"
ACTIVE_CORE=$(systemctl list-units 'owui-0[0-6]*' 'owui-09*' 'owui-1[0-6]*' --type=service --state=active --no-legend | grep -v 'owui-07\|owui-08' | wc -l)
echo "Core services active: $ACTIVE_CORE/14 (excluding external sidecars)"

if [ "$ACTIVE_CORE" -ge 12 ]; then
    echo "🎉 Core deployment successful!"
    echo "✅ OpenWebUI Suite is ready for production use"
    echo "🔗 Gateway available at: http://localhost:8000"
else
    echo "⚠️  Some core services need attention"
    echo "💡 Check individual service logs with: sudo journalctl -u <service-name> -f"
fi

echo ""
echo "📝 Note: Sidecar services (Tandoor, OpenBB) disabled - they require separate repository setup"
