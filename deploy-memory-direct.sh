#!/bin/bash
# Memory Service Deployment Script - Cache Bypass Version
# This version forces creation of standalone Dockerfile

TEMP_DIR="/tmp/owui-memory-deploy-$(date +%s)"

echo "🧠 Memory Service Deployment (Cache Bypass)"
echo "==========================================="

# Create temp directory with timestamp
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Download the memory service package
echo "📦 Downloading memory service package..."
curl -L -o memory-service.zip "https://raw.githubusercontent.com/rcmiller01/OpenWebUI_Suite/main/memory-service.zip?$(date +%s)"

if [ ! -f memory-service.zip ]; then
    echo "❌ Failed to download memory-service.zip"
    exit 1
fi

# Extract the service files
echo "📂 Extracting service files..."
unzip -o memory-service.zip

# List what we have
echo "📁 Extracted files:"
ls -la

# FORCE creation of standalone Dockerfile (overwrite anything)
echo "🔧 Creating standalone Dockerfile (forced)..."
rm -f Dockerfile  # Remove any existing Dockerfile first

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

# Verify we created the right Dockerfile
echo "🔍 Verifying Dockerfile content:"
echo "First few lines of Dockerfile:"
head -5 Dockerfile

# Verify required files
echo "🔍 Verifying required files..."
for file in requirements.txt src/app.py start.py; do
    if [ ! -f "$file" ]; then
        echo "❌ $file not found"
        exit 1
    else
        echo "✅ $file found"
    fi
done

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t owui/memory-2.0:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    echo "📋 Dockerfile content:"
    cat Dockerfile
    exit 1
fi

# Stop and remove existing container
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

# Wait and health check
echo "⏳ Waiting for service to start..."
sleep 15

echo "🔍 Testing service health..."
for i in {1..5}; do
    if curl -f http://localhost:8102/healthz >/dev/null 2>&1; then
        echo "✅ Memory service deployed successfully!"
        echo "🌐 Service available at: http://$(hostname -I | awk '{print $1}'):8102"
        echo "🔗 Health check: http://$(hostname -I | awk '{print $1}'):8102/healthz"
        
        # Test the health endpoint
        echo "🔍 Health endpoint response:"
        curl -s http://localhost:8102/healthz
        echo ""
        break
    else
        echo "⏳ Attempt $i/5: Service not ready yet..."
        if [ $i -eq 5 ]; then
            echo "❌ Health check failed - debugging..."
            echo "📋 Container status:"
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
