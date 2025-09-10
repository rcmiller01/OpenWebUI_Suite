# OpenWebUI Suite Service Manager (Local Development)

param(
    [string]$Command = "help",
    [string]$Service = "",
    [int]$Lines = 50
)

# Service definitions
$Services = @{
    "00-pipelines-gateway" = @{ Port = 8088; Description = "OWUI Pipelines Gateway" }
    "01-intent-router" = @{ Port = 8101; Description = "Intent Router" }
    "02-memory-2.0" = @{ Port = 8102; Description = "Memory Service" }
    "03-feeling-engine" = @{ Port = 8103; Description = "Feeling Engine" }
    "04-hidden-multi-expert-merger" = @{ Port = 8104; Description = "Multi Expert Merger" }
    "05-drive-state" = @{ Port = 8105; Description = "Drive State" }
    "06-byof-tool-hub" = @{ Port = 8106; Description = "BYOF Tool Hub" }
    "07-tandoor-sidecar" = @{ Port = 8107; Description = "Tandoor Sidecar" }
    "08-openbb-sidecar" = @{ Port = 8108; Description = "OpenBB Sidecar" }
    "09-proactive-daemon" = @{ Port = 0; Description = "Proactive Daemon Worker" }
    "10-multimodal-router" = @{ Port = 8110; Description = "Multimodal Router" }
    "11-stt-tts-gateway" = @{ Port = 8111; Description = "STT-TTS Gateway" }
    "12-avatar-overlay" = @{ Port = 8112; Description = "Avatar Overlay" }
    "13-policy-guardrails" = @{ Port = 8113; Description = "Policy Guardrails" }
    "14-telemetry-cache" = @{ Port = 8114; Description = "Telemetry Cache" }
    "16-fastvlm-sidecar" = @{ Port = 8115; Description = "FastVLM Sidecar" }
}

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    switch ($Type) {
        "Success" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Warning" { Write-Host "⚠️  $Message" -ForegroundColor Yellow }
        "Error" { Write-Host "❌ $Message" -ForegroundColor Red }
        "Info" { Write-Host "ℹ️  $Message" -ForegroundColor Blue }
        default { Write-Host "🔧 $Message" -ForegroundColor Cyan }
    }
}

function Discover-Services {
    Write-Status "Discovering OpenWebUI Suite services..." "Info"
    Write-Host ""
    
    $format = "{0,-25} {1,-8} {2,-12} {3}"
    Write-Host ($format -f "SERVICE", "PORT", "STATUS", "DESCRIPTION") -ForegroundColor White
    Write-Host ($format -f "-------", "----", "------", "-----------") -ForegroundColor Gray
    
    foreach ($serviceDir in $Services.Keys | Sort-Object) {
        $service = $Services[$serviceDir]
        $port = $service.Port
        $description = $service.Description
        
        # Check if service directory exists
        if (!(Test-Path ".\$serviceDir")) {
            Write-Host ($format -f $serviceDir, $port, "MISSING", $description) -ForegroundColor Red
            continue
        }
        
        # Check if service is running (port listening)
        $status = "STOPPED"
        if ($port -gt 0) {
            try {
                $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop | Select-Object -First 1
                if ($connection) {
                    $status = "RUNNING"
                }
            } catch {
                $status = "STOPPED"
            }
        } else {
            # For worker processes, check if Python process exists
            $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
                $_.Path -like "*$serviceDir*" -or $_.CommandLine -like "*$serviceDir*" 
            }
            if ($pythonProcesses) {
                $status = "RUNNING"
            }
        }
        
        $color = switch ($status) {
            "RUNNING" { "Green" }
            "STOPPED" { "Yellow" }
            default { "Red" }
        }
        
        Write-Host ($format -f $serviceDir, $port, $status, $description) -ForegroundColor $color
    }
}

function Test-ServiceHealth {
    param([string]$ServiceDir = "")
    
    if ($ServiceDir) {
        $servicesToCheck = @{$ServiceDir = $Services[$ServiceDir]}
    } else {
        $servicesToCheck = $Services
        Write-Status "Running health checks on all services..." "Info"
        Write-Host ""
        
        $format = "{0,-25} {1,-8} {2}"
        Write-Host ($format -f "SERVICE", "PORT", "HEALTH") -ForegroundColor White
        Write-Host ($format -f "-------", "----", "------") -ForegroundColor Gray
    }
    
    foreach ($serviceDir in $servicesToCheck.Keys | Sort-Object) {
        $service = $servicesToCheck[$serviceDir]
        $port = $service.Port
        
        if (!(Test-Path ".\$serviceDir")) {
            if (!$ServiceDir) {
                Write-Host ($format -f $serviceDir, $port, "MISSING") -ForegroundColor Red
            } else {
                Write-Status "Service directory not found: .\$serviceDir" "Error"
            }
            continue
        }
        
        if ($port -eq 0) {
            # Worker process check
            $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
                $_.Path -like "*$serviceDir*" -or $_.CommandLine -like "*$serviceDir*" 
            }
            $health = if ($pythonProcesses) { "RUNNING" } else { "STOPPED" }
            $color = if ($pythonProcesses) { "Green" } else { "Red" }
            
            if (!$ServiceDir) {
                Write-Host ($format -f $serviceDir, "worker", $health) -ForegroundColor $color
            } else {
                Write-Status "$serviceDir (worker): $health" $(if ($pythonProcesses) { "Success" } else { "Error" })
            }
        } else {
            # HTTP service check
            $endpoints = @("/healthz", "/health", "/")
            $healthy = $false
            
            foreach ($endpoint in $endpoints) {
                try {
                    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port$endpoint" -TimeoutSec 2 -ErrorAction Stop
                    $healthy = $true
                    break
                } catch {
                    # Continue to next endpoint
                }
            }
            
            if (!$ServiceDir) {
                $healthStatus = if ($healthy) { "HEALTHY" } else { "UNHEALTHY" }
                $color = if ($healthy) { "Green" } else { "Red" }
                Write-Host ($format -f $serviceDir, $port, $healthStatus) -ForegroundColor $color
            } else {
                if ($healthy) {
                    Write-Status "$serviceDir (:$port): Healthy" "Success"
                } else {
                    Write-Status "$serviceDir (:$port): Not responding" "Error"
                    
                    # Check if port is listening
                    try {
                        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop | Select-Object -First 1
                        if ($connection) {
                            Write-Status "Port $port is listening but not responding to HTTP" "Warning"
                        }
                    } catch {
                        Write-Status "Port $port is not listening" "Warning"
                    }
                }
            }
        }
    }
}

function Start-LocalService {
    param([string]$ServiceDir)
    
    if (!(Test-Path ".\$serviceDir")) {
        Write-Status "Service directory not found: .\$serviceDir" "Error"
        return
    }
    
    $service = $Services[$ServiceDir]
    $port = $service.Port
    
    Write-Status "Starting $ServiceDir locally..." "Info"
    
    Push-Location ".\$serviceDir"
    
    try {
        # Create data directory if needed
        if ($ServiceDir -match "(gateway|memory|policy|telemetry)") {
            if (!(Test-Path "data")) {
                New-Item -ItemType Directory -Path "data" -Force | Out-Null
                Write-Status "Created data directory for $ServiceDir" "Success"
            }
        }
        
        if ($port -eq 0) {
            # Worker process
            Write-Status "Starting worker process..." "Info"
            Start-Process python -ArgumentList "src/worker.py" -NoNewWindow
        } else {
            # HTTP service
            Write-Status "Starting HTTP service on port $port..." "Info"
            $args = @("src.server:app", "--host", "127.0.0.1", "--port", $port, "--reload")
            Start-Process python -ArgumentList @("-m", "uvicorn") + $args -NoNewWindow
        }
        
        Start-Sleep 3
        Write-Status "$ServiceDir started" "Success"
        
    } catch {
        Write-Status "Failed to start ${ServiceDir}: $($_.Exception.Message)" "Error"
    } finally {
        Pop-Location
    }
}

function Show-ServiceHelp {
    Write-Host @"
OpenWebUI Suite Service Manager (Local Development)

Usage: .\owui-service-manager.ps1 -Command <command> [-Service <service>] [-Lines <number>]

Commands:
  discover          Show all services and their status
  health            Check health of all services or specific service
  start             Start a specific service locally
  help              Show this help

Parameters:
  -Service          Specific service name (required for start command)
  -Lines            Number of log lines to show (default: 50)

Available services:
$($Services.Keys | Sort-Object | ForEach-Object { "  $_" } | Out-String)

Examples:
  .\owui-service-manager.ps1 -Command discover
  .\owui-service-manager.ps1 -Command health
  .\owui-service-manager.ps1 -Command health -Service "00-pipelines-gateway"
  .\owui-service-manager.ps1 -Command start -Service "00-pipelines-gateway"
"@
}

# Main script logic
switch ($Command.ToLower()) {
    "discover" { 
        Discover-Services 
    }
    "health" { 
        Test-ServiceHealth -ServiceDir $Service 
    }
    "start" { 
        if (!$Service) {
            Write-Status "Service parameter required for start command" "Error"
            Write-Host "Available services: $($Services.Keys -join ', ')"
            exit 1
        }
        if (!$Services.ContainsKey($Service)) {
            Write-Status "Unknown service: $Service" "Error"
            Write-Host "Available services: $($Services.Keys -join ', ')"
            exit 1
        }
        Start-LocalService -ServiceDir $Service 
    }
    "help" { 
        Show-ServiceHelp 
    }
    default { 
        Write-Status "Unknown command: $Command" "Error"
        Show-ServiceHelp 
    }
}
