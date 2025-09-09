#!/bin/bash
# Commands to deploy Memory 2.0 service on Docker host (192.168.50.15)
# Run these commands on your Docker host after copying memory-service.zip

echo "🧠 Deploying Memory 2.0 service..."

# Extract the service files
cd /tmp
unzip -o memory-service.zip
cd 02-memory-2.0

# Build the Docker image
echo "Building Docker image..."
docker build -t owui/memory-2.0:latest .

# Stop and remove existing container if it exists
echo "Stopping existing container..."
docker stop memory-service 2>/dev/null || true
docker rm memory-service 2>/dev/null || true

# Run the new container
echo "Starting Memory service container..."
docker run -d \
  --name memory-service \
  --restart unless-stopped \
  -p 8102:8102 \
  owui/memory-2.0:latest

# Wait for service to start
echo "Waiting for service to start..."
sleep 10

# Health check
echo "Testing service health..."
curl -f http://localhost:8102/healthz || echo "❌ Health check failed"

echo "✅ Memory service deployment complete!"
echo "Service available at: http://192.168.50.15:8102"
