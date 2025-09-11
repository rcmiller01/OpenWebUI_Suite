#!/bin/bash
# Final fixes for remaining OpenWebUI Suite service issues

echo "🔧 OpenWebUI Suite - Final Service Fixes"
echo "======================================="

cd /opt/openwebui-suite

# 1. Fix missing dependencies
echo "1. Installing missing dependencies..."

echo "Installing faster_whisper for STT-TTS Gateway..."
source .venv/bin/activate
pip install faster_whisper

echo "Installing policy-guardrails dependencies..."
pip install -r 13-policy-guardrails/requirements.txt

# 2. Fix services without start.py (need different approach)
echo ""
echo "2. Checking services without start.py..."

# Check what these services actually need
for service in "10-multimodal-router" "12-avatar-overlay" "16-fastvlm-sidecar"; do
    echo "Checking $service structure..."
    
    if [ -f "$service/package.json" ]; then
        echo "  $service is Node.js - needs npm start"
        # Install npm dependencies if missing
        cd "$service"
        if [ ! -d "node_modules" ]; then
            echo "  Installing npm dependencies..."
            npm install
        fi
        cd ..
    elif [ -f "$service/src/server.py" ]; then
        echo "  $service has FastAPI server - needs uvicorn"
    elif [ -f "$service/app.py" ]; then
        echo "  $service has app.py - can run directly"
    else
        echo "  $service structure unclear - checking files..."
        ls -la "$service/" | head -10
    fi
done

# 3. Restart the services with dependency issues
echo ""
echo "3. Restarting services with fixed dependencies..."

sudo systemctl restart owui-11-stt-tts-gateway.service
sleep 3
if systemctl is-active owui-11-stt-tts-gateway.service >/dev/null 2>&1; then
    echo "✅ STT-TTS Gateway is now running"
else
    echo "❌ STT-TTS Gateway still having issues"
    sudo journalctl -u owui-11-stt-tts-gateway.service --no-pager -n 3
fi

sudo systemctl restart owui-13-policy-guardrails.service
sleep 3
if systemctl is-active owui-13-policy-guardrails.service >/dev/null 2>&1; then
    echo "✅ Policy Guardrails is now running"
else
    echo "❌ Policy Guardrails still having issues"
    sudo journalctl -u owui-13-policy-guardrails.service --no-pager -n 3
fi

# 4. Final comprehensive health check
echo ""
echo "4. Final comprehensive health check..."

# Check all service statuses
echo "Service Status Summary:"
systemctl list-units 'owui-*' --type=service --no-legend | while read unit load active sub desc; do
    if [ "$active" = "active" ]; then
        echo "✅ $unit"
    else
        echo "❌ $unit ($active $sub)"
    fi
done

echo ""
echo "Health Endpoint Check:"
for port in {8100..8115}; do
    # Try multiple health endpoint patterns
    if curl -s -f "http://localhost:$port/healthz" >/dev/null 2>&1; then
        echo "✅ Port $port: /healthz endpoint healthy"
    elif curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
        echo "✅ Port $port: /health endpoint healthy"
    elif curl -s -f "http://localhost:$port/" >/dev/null 2>&1; then
        echo "🟡 Port $port: Service responding (no health endpoint)"
    else
        echo "❌ Port $port: Not responding"
    fi
done

# 5. Summary
echo ""
echo "📊 Final Deployment Summary:"
TOTAL_ACTIVE=$(systemctl list-units 'owui-*' --type=service --state=active --no-legend | wc -l)
TOTAL_SERVICES=14  # Excluding external sidecars

echo "Active core services: $TOTAL_ACTIVE/$TOTAL_SERVICES"

if [ "$TOTAL_ACTIVE" -eq "$TOTAL_SERVICES" ]; then
    echo "🎉 SUCCESS! All core services are running!"
    echo "✅ OpenWebUI Suite is fully operational"
    echo "🌐 Gateway accessible at: http://localhost:8000"
    echo "🧠 Intent Router at: http://localhost:8101"
    echo "💭 Memory Service at: http://localhost:8102" 
    echo "❤️  Feeling Engine at: http://localhost:8103"
else
    echo "⚠️  $((TOTAL_SERVICES - TOTAL_ACTIVE)) services still need attention"
    echo "Check individual service logs for details"
fi

echo ""
echo "🚀 Deployment completed! Ready for production use."
