# Fix for SQLite database directory issue in 00-pipelines-gateway
Write-Host "🔧 Fixing gateway database directory issue..." -ForegroundColor Yellow

# Create the data directory in the application path
Write-Host "Creating database directory..." -ForegroundColor Blue
$dataDir = ".\00-pipelines-gateway\data"
if (!(Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "✅ Created directory: $dataDir" -ForegroundColor Green
} else {
    Write-Host "✅ Directory already exists: $dataDir" -ForegroundColor Green
}

# Set environment variable for local development
Write-Host "Setting GATEWAY_DB environment variable..." -ForegroundColor Blue
$envFile = ".\.env"
$gatewayDbPath = "GATEWAY_DB=./00-pipelines-gateway/data/gateway.db"

if (Test-Path $envFile) {
    $content = Get-Content $envFile
    if ($content -match "^GATEWAY_DB=") {
        $content = $content -replace "^GATEWAY_DB=.*", $gatewayDbPath
        $content | Set-Content $envFile
        Write-Host "✅ Updated GATEWAY_DB in .env file" -ForegroundColor Green
    } else {
        Add-Content $envFile "`n$gatewayDbPath"
        Write-Host "✅ Added GATEWAY_DB to .env file" -ForegroundColor Green
    }
} else {
    $gatewayDbPath | Set-Content $envFile
    Write-Host "✅ Created .env file with GATEWAY_DB" -ForegroundColor Green
}

Write-Host "✅ Database fix applied for local development." -ForegroundColor Green
Write-Host "📍 Database location: ./00-pipelines-gateway/data/gateway.db" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 To apply to production server, use fix-gateway-db.sh" -ForegroundColor Yellow
