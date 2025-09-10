# OpenWebUI Suite Service Diagnostics (Windows/Local)

Write-Host "🔍 OpenWebUI Suite Service Diagnostics" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🏥 Service Health Check:" -ForegroundColor Yellow
Write-Host "------------------------" -ForegroundColor Yellow

# Check each service port
$services = @{
    "8088" = "Gateway"
    "8101" = "Intent Router"
    "8102" = "Memory"
    "8103" = "Feeling Engine"
    "8110" = "Multimodal Router"
    "8111" = "STT-TTS Gateway"
    "8112" = "Avatar Overlay"
    "8113" = "Policy Guardrails"
    "8114" = "Telemetry Cache"
    "8115" = "FastVLM Sidecar"
}

foreach ($port in $services.Keys) {
    $name = $services[$port]
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/healthz" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✅ $name ($port): Healthy" -ForegroundColor Green
    } catch {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2 -ErrorAction Stop
            Write-Host "  ✅ $name ($port): Healthy (alt endpoint)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ $name ($port): Not responding" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "🗃️ Database Status:" -ForegroundColor Yellow
Write-Host "------------------" -ForegroundColor Yellow

$dbPath = ".\00-pipelines-gateway\data\gateway.db"
if (Test-Path $dbPath) {
    Write-Host "  ✅ Database file exists: $dbPath" -ForegroundColor Green
    $dbInfo = Get-Item $dbPath
    Write-Host "    Size: $($dbInfo.Length) bytes, Modified: $($dbInfo.LastWriteTime)" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Database file missing: $dbPath" -ForegroundColor Red
    
    $dbDir = Split-Path $dbPath -Parent
    if (Test-Path $dbDir) {
        Write-Host "  📁 Directory exists but database missing" -ForegroundColor Yellow
        Write-Host "    Directory contents:" -ForegroundColor Gray
        Get-ChildItem $dbDir | ForEach-Object { Write-Host "      $($_.Name)" -ForegroundColor Gray }
    } else {
        Write-Host "  📁 Database directory doesn't exist: $dbDir" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "⚙️ Environment Configuration:" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "  📄 .env file exists" -ForegroundColor Green
    $envContent = Get-Content ".env" | Where-Object { $_ -match "GATEWAY|DB" }
    if ($envContent) {
        Write-Host "    Database-related settings:" -ForegroundColor Gray
        foreach ($line in $envContent) {
            Write-Host "      $line" -ForegroundColor Gray
        }
    } else {
        Write-Host "    No database-related settings found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ .env file missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "🌐 Port Availability:" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow

foreach ($port in $services.Keys) {
    $name = $services[$port]
    try {
        $listener = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop | Select-Object -First 1
        if ($listener) {
            Write-Host "  🔌 Port $port ($name): In use (PID: $($listener.OwningProcess))" -ForegroundColor Blue
        }
    } catch {
        Write-Host "  🔌 Port $port ($name): Available" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "💡 Local Troubleshooting Steps:" -ForegroundColor Magenta
Write-Host "------------------------------" -ForegroundColor Magenta
Write-Host "  1. Check if database directory exists:" -ForegroundColor White
Write-Host "     Test-Path '.\00-pipelines-gateway\data'" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Create database directory if missing:" -ForegroundColor White
Write-Host "     New-Item -ItemType Directory -Path '.\00-pipelines-gateway\data' -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test gateway service manually:" -ForegroundColor White
Write-Host "     cd .\00-pipelines-gateway" -ForegroundColor Gray
Write-Host "     python -m uvicorn src.server:app --host 127.0.0.1 --port 8088 --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Check Python environment:" -ForegroundColor White
Write-Host "     python --version" -ForegroundColor Gray
Write-Host "     pip list | findstr fastapi" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Install missing dependencies:" -ForegroundColor White
Write-Host "     pip install fastapi uvicorn sqlite3" -ForegroundColor Gray
