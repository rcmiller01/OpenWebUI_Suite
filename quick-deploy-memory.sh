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

# Check what was extracted and work with the files
echo "📁 Files extracted. Working directory contents:"
ls -la

# Always create our standalone Dockerfile (overwrite the original)
echo "🔧 Creating standalone Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY start.py ./start.py

EXPOSE 8102

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8102/healthz || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8102"]
EOF

# Verify we have the required files
echo "🔍 Verifying required files..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

if [ ! -f "src/app.py" ]; then
    echo "❌ src/app.py not found"
    exit 1
fi

if [ ! -f "start.py" ]; then
    echo "❌ start.py not found"
    exit 1
fi

echo "✅ All required files found"

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t owui/memory-2.0:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

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

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container"
    exit 1
fi

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 15

# Health check with retries
echo "🔍 Testing service health..."
for i in {1..5}; do
    if curl -f http://localhost:8102/healthz >/dev/null 2>&1; then
        echo "✅ Memory service deployed successfully!"
        echo "🌐 Service available at: http://$(hostname -I | awk '{print $1}'):8102"
        echo "🔗 Health check: http://$(hostname -I | awk '{print $1}'):8102/healthz"
        break
    else
        echo "⏳ Attempt $i/5: Service not ready yet..."
        if [ $i -eq 5 ]; then
            echo "❌ Health check failed - checking container status..."
            docker ps | grep memory-service
            echo "📋 Container logs:"
            docker logs memory-service
        else
            sleep 5
        fi
    fi
done

# Cleanup
cd /
rm -rf $TEMP_DIR

echo "🎉 Deployment complete!"
