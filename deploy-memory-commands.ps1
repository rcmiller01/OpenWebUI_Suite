# PowerShell commands to deploy Memory 2.0 service on Docker host
# Run these commands on your Docker host after copying memory-service.zip

Write-Host "🧠 Deploying Memory 2.0 service..." -ForegroundColor Green

# Extract the service files
Set-Location C:\temp
Expand-Archive -Path memory-service.zip -DestinationPath . -Force
Set-Location 02-memory-2.0

# Build the Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t owui/memory-2.0:latest .

# Stop and remove existing container if it exists
Write-Host "Stopping existing container..." -ForegroundColor Yellow
docker stop memory-service 2>$null
docker rm memory-service 2>$null

# Run the new container
Write-Host "Starting Memory service container..." -ForegroundColor Yellow
docker run -d `
  --name memory-service `
  --restart unless-stopped `
  -p 8102:8102 `
  owui/memory-2.0:latest

# Wait for service to start
Write-Host "Waiting for service to start..." -ForegroundColor Yellow
Start-Sleep 10

# Health check
Write-Host "Testing service health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8102/healthz" -UseBasicParsing
    Write-Host "✅ Health check passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed" -ForegroundColor Red
}

Write-Host "✅ Memory service deployment complete!" -ForegroundColor Green
Write-Host "Service available at: http://192.168.50.15:8102" -ForegroundColor Cyan
