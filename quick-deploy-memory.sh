#!/bin/bash
# Quick Memory Service Deployment Script
# Run this on your Docker host to deploy the Memory 2.0 service

GITHUB_REPO="https://raw.githubusercontent.com/rcmiller01/OpenWebUI_Suite/main"
TEMP_DIR="/tmp/owui-memory-deploy"

echo "🧠 Quick Memory Service Deployment"
echo "=================================="

# Create temp directory
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Download the memory service package
echo "📦 Downloading memory service package..."
curl -L -o memory-service.zip "$GITHUB_REPO/memory-service.zip"
if [ ! -f memory-service.zip ]; then
    echo "❌ Failed to download memory-service.zip"
    exit 1
fi

# Extract the service files
echo "📂 Extracting service files..."
unzip -o memory-service.zip
cd 02-memory-2.0

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t owui/memory-2.0:latest .

# Stop and remove existing container if it exists
echo "🛑 Stopping existing container..."
docker stop memory-service 2>/dev/null || true
docker rm memory-service 2>/dev/null || true

# Run the new container
echo "🚀 Starting Memory service container..."
docker run -d \
  --name memory-service \
  --restart unless-stopped \
  -p 8102:8102 \
  owui/memory-2.0:latest

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 10

# Health check
echo "🔍 Testing service health..."
if curl -f http://localhost:8102/healthz >/dev/null 2>&1; then
    echo "✅ Memory service deployed successfully!"
    echo "🌐 Service available at: http://$(hostname -I | awk '{print $1}'):8102"
    echo "🔗 Health check: http://$(hostname -I | awk '{print $1}'):8102/healthz"
else
    echo "❌ Health check failed - service may not be ready"
    echo "📋 Check container logs: docker logs memory-service"
fi

# Cleanup
cd /
rm -rf $TEMP_DIR

echo "🎉 Deployment complete!"
