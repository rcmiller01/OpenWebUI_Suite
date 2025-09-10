#!/bin/bash
# Diagnostic script for OpenWebUI Suite service startup issues

echo "🔍 OpenWebUI Suite Service Diagnostics"
echo "======================================"

# Check if we're on the server
if [ -d "/opt/openwebui-suite" ]; then
    echo "📍 Running on production server"
    BASE_DIR="/opt/openwebui-suite"
else
    echo "📍 Running locally"
    BASE_DIR="."
fi

echo ""
echo "🏥 Service Health Check:"
echo "------------------------"

# Check each service port
services=("8088:Gateway" "8101:Intent" "8102:Memory" "8103:Feeling" "8110:Multimodal" "8111:STT-TTS" "8112:Avatar" "8113:Policy" "8114:Telemetry" "8115:FastVLM")

for service in "${services[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"
    
    if curl -s -f "http://127.0.0.1:${port}/healthz" >/dev/null 2>&1; then
        echo "  ✅ ${name} (${port}): Healthy"
    elif curl -s -f "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
        echo "  ✅ ${name} (${port}): Healthy (alt endpoint)"
    else
        echo "  ❌ ${name} (${port}): Not responding"
    fi
done

echo ""
echo "🔧 Systemd Service Status:"
echo "-------------------------"
if command -v systemctl >/dev/null 2>&1; then
    systemctl --no-pager status owui-00-pipelines-gateway.service | head -15
else
    echo "  ℹ️  Systemctl not available (not on production server)"
fi

echo ""
echo "📋 Recent Gateway Logs:"
echo "----------------------"
if [ -d "/opt/openwebui-suite" ]; then
    # Production server - check systemd logs
    echo "  📄 Last 10 lines from systemd journal:"
    journalctl -u owui-00-pipelines-gateway.service -n 10 --no-pager
else
    echo "  ℹ️  Local environment - check application logs manually"
fi

echo ""
echo "🗃️ Database Status:"
echo "------------------"
if [ -f "${BASE_DIR}/00-pipelines-gateway/data/gateway.db" ]; then
    echo "  ✅ Database file exists: ${BASE_DIR}/00-pipelines-gateway/data/gateway.db"
    ls -la "${BASE_DIR}/00-pipelines-gateway/data/gateway.db"
elif [ -f "${BASE_DIR}/.env" ] && grep -q "GATEWAY_DB" "${BASE_DIR}/.env"; then
    DB_PATH=$(grep "GATEWAY_DB" "${BASE_DIR}/.env" | cut -d'=' -f2)
    if [ -f "$DB_PATH" ]; then
        echo "  ✅ Database file exists: $DB_PATH"
        ls -la "$DB_PATH"
    else
        echo "  ❌ Database file missing: $DB_PATH"
        echo "  📁 Directory status:"
        ls -la "$(dirname "$DB_PATH")" 2>/dev/null || echo "    Directory doesn't exist"
    fi
else
    echo "  ❌ No database configuration found"
fi

echo ""
echo "🌐 Network & Port Status:"
echo "------------------------"
if command -v netstat >/dev/null 2>&1; then
    echo "  📡 Services listening on configured ports:"
    netstat -tlnp | grep -E ':(8088|8101|8102|8103|8110|8111|8112|8113|8114|8115)\s'
elif command -v ss >/dev/null 2>&1; then
    echo "  📡 Services listening on configured ports:"
    ss -tlnp | grep -E ':(8088|8101|8102|8103|8110|8111|8112|8113|8114|8115)\s'
else
    echo "  ℹ️  Network diagnostic tools not available"
fi

echo ""
echo "💡 Troubleshooting Suggestions:"
echo "------------------------------"
echo "  1. Check service logs: journalctl -u owui-00-pipelines-gateway.service -f"
echo "  2. Verify database permissions: ls -la /opt/openwebui-suite/00-pipelines-gateway/data/"
echo "  3. Test manual startup: cd /opt/openwebui-suite/00-pipelines-gateway && python -m uvicorn src.server:app --host 0.0.0.0 --port 8088"
echo "  4. Check environment variables: cat /opt/openwebui-suite/.env | grep -E '(GATEWAY|DB)'"
echo "  5. Restart service: sudo systemctl restart owui-00-pipelines-gateway.service"
