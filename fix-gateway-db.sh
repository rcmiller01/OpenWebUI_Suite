#!/bin/bash
# Fix for SQLite database directory issue in 00-pipelines-gateway

echo "🔧 Fixing gateway database directory issue..."

# Stop the service if running
echo "Stopping gateway service..."
sudo systemctl stop owui-00-pipelines-gateway.service 2>/dev/null || true

# Create the data directory in the application path
echo "Creating database directory..."
sudo mkdir -p /opt/openwebui-suite/00-pipelines-gateway/data
sudo chown -R $(whoami):$(whoami) /opt/openwebui-suite/00-pipelines-gateway/data
sudo chmod 755 /opt/openwebui-suite/00-pipelines-gateway/data

# Set environment variable for the service
echo "Setting GATEWAY_DB environment variable..."
if [ ! -f /opt/openwebui-suite/.env ]; then
    echo "GATEWAY_DB=/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db" | sudo tee -a /opt/openwebui-suite/.env
else
    # Update or add GATEWAY_DB to .env file
    if grep -q "^GATEWAY_DB=" /opt/openwebui-suite/.env; then
        sudo sed -i 's|^GATEWAY_DB=.*|GATEWAY_DB=/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db|' /opt/openwebui-suite/.env
    else
        echo "GATEWAY_DB=/opt/openwebui-suite/00-pipelines-gateway/data/gateway.db" | sudo tee -a /opt/openwebui-suite/.env
    fi
fi

# Restart the service
echo "Starting gateway service..."
sudo systemctl start owui-00-pipelines-gateway.service

# Check status
sleep 3
echo "Service status:"
sudo systemctl status owui-00-pipelines-gateway.service --no-pager -l

echo "✅ Database fix applied. The gateway should now start successfully."
echo "📍 Database location: /opt/openwebui-suite/00-pipelines-gateway/data/gateway.db"
