#!/bin/bash
# Quick fix for production server database issues

echo "🔧 Quick Fix for Gateway Database Issues"
echo "========================================"

# Stop the service
echo "⏹️  Stopping gateway service..."
sudo systemctl stop owui-00-pipelines-gateway.service

# Ensure the database directory exists with proper permissions
echo "📁 Creating database directory..."
sudo mkdir -p /opt/openwebui-suite/00-pipelines-gateway/data
sudo chown -R $(whoami):$(whoami) /opt/openwebui-suite/00-pipelines-gateway/data
sudo chmod 755 /opt/openwebui-suite/00-pipelines-gateway/data

# Test database creation
echo "🗃️  Testing database creation..."
cd /opt/openwebui-suite/00-pipelines-gateway
python3 -c "
import sqlite3
import os
os.makedirs('./data', exist_ok=True)
conn = sqlite3.connect('./data/gateway.db')
print('✅ Database test successful')
conn.close()
"

# Update environment configuration
echo "⚙️  Updating environment configuration..."
if ! grep -q "GATEWAY_DB" /opt/openwebui-suite/.env 2>/dev/null; then
    echo "GATEWAY_DB=/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db" | sudo tee -a /opt/openwebui-suite/.env
    echo "✅ Added GATEWAY_DB to .env"
else
    sudo sed -i 's|^GATEWAY_DB=.*|GATEWAY_DB=/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db|' /opt/openwebui-suite/.env
    echo "✅ Updated GATEWAY_DB in .env"
fi

# Test the projects module
echo "🧪 Testing projects module..."
cd /opt/openwebui-suite/00-pipelines-gateway
python3 -c "
try:
    from src.projects import _init
    _init()
    print('✅ Projects module test successful')
except Exception as e:
    print(f'❌ Projects module test failed: {e}')
"

# Start the service
echo "▶️  Starting gateway service..."
sudo systemctl start owui-00-pipelines-gateway.service

# Wait a moment for startup
sleep 3

# Check service status
echo "📊 Service status:"
sudo systemctl --no-pager status owui-00-pipelines-gateway.service

# Test health endpoint
echo ""
echo "🏥 Testing health endpoint..."
if curl -f http://127.0.0.1:8088/healthz 2>/dev/null; then
    echo "✅ Gateway health check successful!"
else
    echo "❌ Gateway health check failed"
    echo "📋 Recent logs:"
    sudo journalctl -u owui-00-pipelines-gateway.service -n 10 --no-pager
fi

echo ""
echo "🎯 Fix complete! Gateway should now be responding on port 8088."
