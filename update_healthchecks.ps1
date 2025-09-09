#!/usr/bin/env pwsh
# Script to update docker-compose healthchecks with correct ports

$file = "docker-compose.unified.yml"
$content = Get-Content $file -Raw

# Service port mappings
$updates = @(
    @{service="06-byof-tool-hub"; port="8106"}
    @{service="07-tandoor-sidecar"; port="8107"}
    @{service="08-openbb-sidecar"; port="8108"}
    @{service="10-multimodal-router"; port="8110"}
    @{service="11-stt-tts-gateway"; port="8111"}
    @{service="12-avatar-overlay"; port="8112"}
    @{service="14-telemetry-cache"; port="8114"}
    @{service="16-fastvlm-sidecar"; port="8115"}
    @{service="openwebui-suite"; port="3000"}
)

foreach ($update in $updates) {
    $service = $update.service
    $port = $update.port
    
    # Pattern to match the service block and replace its healthcheck
    $pattern = "($service:.*?healthcheck:\s*test: \[`"CMD-SHELL`", `"python -c 'import socket; exit\(0\)'`"\])"
    $replacement = "`$1".Replace("python -c 'import socket; exit(0)'", "curl -f http://localhost:$port/healthz || exit 1")
    
    $content = $content -replace $pattern, $replacement, "Singleline"
}

# Special case for 09-proactive-daemon (worker service)
$content = $content -replace "(09-proactive-daemon:.*?healthcheck:\s*test: \[`"CMD-SHELL`", `"python -c 'import socket; exit\(0\)'`"\])", 
    "`$1".Replace("python -c 'import socket; exit(0)'", "pgrep -f 'src/worker.py' || exit 1")

$content | Set-Content $file

Write-Host "Updated healthchecks in $file"
