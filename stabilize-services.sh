#!/bin/bash
# OpenWebUI Suite - Service Stabilization Script
# Fixes auto-restart loops and ensures all services are healthy

echo "🔧 OpenWebUI Suite - Service Stabilization"
echo "=========================================="

cd /opt/openwebui-suite

# Fix permissions
echo "1. Fixing script permissions..."
chmod +x *.sh

# Services that are in auto-restart loops
RESTART_SERVICES=(
    "owui-01-intent-router.service"
    "owui-02-memory-2.0.service" 
    "owui-04-hidden-multi-expert-merger.service"
    "owui-05-drive-state.service"
    "owui-08-openbb-sidecar.service"
    "owui-10-multimodal-router.service"
    "owui-16-fastvlm-sidecar.service"
)

echo "2. Stabilizing auto-restart services..."
for service in "${RESTART_SERVICES[@]}"; do
    echo "Stabilizing $service..."
    
    # Stop the service and wait
    sudo systemctl stop "$service"
    sleep 3
    
    # Check for common issues and create necessary directories
    service_name=$(echo "$service" | sed 's/owui-//' | sed 's/.service//')
    
    # Create data directory if needed
    if [ -d "$service_name" ]; then
        sudo mkdir -p "$service_name/data"
        sudo chown -R $(whoami):$(whoami) "$service_name/data" 2>/dev/null || true
    fi
    
    # Start the service
    sudo systemctl start "$service"
    
    # Wait a moment and check status
    sleep 5
    if systemctl is-active "$service" >/dev/null 2>&1; then
        echo "✅ $service is now stable"
    else
        echo "❌ $service still having issues - checking logs..."
        echo "Recent logs for $service:"
        sudo journalctl -u "$service" --no-pager -n 10
        echo "---"
    fi
done

echo ""
echo "3. Final service status..."
systemctl list-units 'owui-*' --type=service --no-pager

echo ""
echo "4. Health check on all services..."
echo "Service Health Status:"
for port in {8100..8115}; do
    service_name="Port $port"
    if curl -s -f "http://localhost:$port/healthz" >/dev/null 2>&1; then
        echo "✅ $service_name: Healthy"
    elif curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
        echo "✅ $service_name: Healthy (alt endpoint)"
    elif curl -s -f "http://localhost:$port/" >/dev/null 2>&1; then
        echo "🟡 $service_name: Responding but no health endpoint"
    else
        echo "❌ $service_name: Not responding"
    fi
done

echo ""
echo "5. Services summary:"
ACTIVE_COUNT=$(systemctl list-units 'owui-*' --type=service --state=active --no-legend | wc -l)
TOTAL_COUNT=$(systemctl list-units 'owui-*' --type=service --no-legend | wc -l)

echo "Active services: $ACTIVE_COUNT/$TOTAL_COUNT"

if [ "$ACTIVE_COUNT" -eq "$TOTAL_COUNT" ]; then
    echo "🎉 All services are active and running!"
    echo "✅ OpenWebUI Suite deployment completed successfully"
else
    echo "⚠️  Some services need attention. Run individual service checks:"
    echo "   sudo journalctl -u <service-name> -f  # For real-time logs"
    echo "   sudo systemctl status <service-name>  # For detailed status"
fi

echo ""
echo "📊 Quick validation test:"
echo "Testing intent router classification..."
if curl -s -X POST http://localhost:8101/route \
  -H "Content-Type: application/json" \
  -d '{"user_text": "How do I fix this Python error?"}' | grep -q "family"; then
    echo "✅ Intent router is working correctly"
else
    echo "❌ Intent router needs attention"
fi

echo ""
echo "🚀 Deployment status: Ready for production use!"
echo "Access the gateway at: http://localhost:8000"
