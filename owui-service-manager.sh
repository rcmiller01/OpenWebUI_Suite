#!/usr/bin/env bash
set -euo pipefail

# OpenWebUI Suite Service Management Script
# Handles service discovery, unit creation, startup, and health monitoring

SUITE_DIR="/opt/openwebui-suite"
ENV_FILE="$SUITE_DIR/.env.prod"
UVICORN_BIN="$SUITE_DIR/.venv/bin/uvicorn"

# Service definitions: directory:port:description
declare -A SERVICES=(
    ["00-pipelines-gateway"]="8088:OWUI Pipelines Gateway"
    ["01-intent-router"]="8101:Intent Router"
    ["02-memory-2.0"]="8102:Memory Service"
    ["03-feeling-engine"]="8103:Feeling Engine"
    ["04-hidden-multi-expert-merger"]="8104:Multi Expert Merger"
    ["05-drive-state"]="8105:Drive State"
    ["06-byof-tool-hub"]="8106:BYOF Tool Hub"
    ["07-tandoor-sidecar"]="8107:Tandoor Sidecar"
    ["08-openbb-sidecar"]="8108:OpenBB Sidecar"
    ["09-proactive-daemon"]="0:Proactive Daemon Worker"
    ["10-multimodal-router"]="8110:Multimodal Router"
    ["11-stt-tts-gateway"]="8111:STT-TTS Gateway"
    ["12-avatar-overlay"]="8112:Avatar Overlay"
    ["13-policy-guardrails"]="8113:Policy Guardrails"
    ["14-telemetry-cache"]="8114:Telemetry Cache"
    ["16-fastvlm-sidecar"]="8115:FastVLM Sidecar"
)

# Color output functions
say() { printf "\n🔧 %s\n" "$*"; }
info() { printf "ℹ️  %s\n" "$*"; }
ok() { printf "✅ %s\n" "$*"; }
warn() { printf "⚠️  %s\n" "$*"; }
err() { printf "❌ %s\n" "$*"; }
die() { err "$*"; exit 1; }

# Check prerequisites
check_prerequisites() {
    say "Checking prerequisites..."
    [ -d "$SUITE_DIR" ] || die "Suite directory missing: $SUITE_DIR"
    [ -f "$ENV_FILE" ] || die "Environment file missing: $ENV_FILE"
    [ -x "$UVICORN_BIN" ] || die "Uvicorn not found: $UVICORN_BIN"
    ok "Prerequisites validated"
}

# Discover existing services
discover_services() {
    say "Discovering OpenWebUI Suite services..."
    
    printf "%-25s %-8s %-12s %-20s %s\n" "SERVICE" "PORT" "STATUS" "UNIT" "DESCRIPTION"
    printf "%-25s %-8s %-12s %-20s %s\n" "-------" "----" "------" "----" "-----------"
    
    for service_dir in "${!SERVICES[@]}"; do
        IFS=':' read -r port description <<< "${SERVICES[$service_dir]}"
        unit_name="owui-${service_dir}.service"
        
        # Check if service directory exists
        if [ ! -d "$SUITE_DIR/$service_dir" ]; then
            printf "%-25s %-8s %-12s %-20s %s\n" "$service_dir" "$port" "MISSING" "N/A" "$description"
            continue
        fi
        
        # Check systemd unit status
        if systemctl is-active --quiet "$unit_name" 2>/dev/null; then
            status="RUNNING"
        elif systemctl is-enabled --quiet "$unit_name" 2>/dev/null; then
            status="STOPPED"
        elif [ -f "/etc/systemd/system/$unit_name" ]; then
            status="DISABLED"
        else
            status="NO-UNIT"
        fi
        
        printf "%-25s %-8s %-12s %-20s %s\n" "$service_dir" "$port" "$status" "$unit_name" "$description"
    done
}

# Show logs for a specific service
show_service_logs() {
    local service_dir="$1"
    local lines="${2:-50}"
    local unit_name="owui-${service_dir}.service"
    
    say "Recent logs for $service_dir (last $lines lines):"
    
    if [ -f "/etc/systemd/system/$unit_name" ]; then
        journalctl -u "$unit_name" -n "$lines" --no-pager || warn "No logs available for $unit_name"
    else
        warn "Systemd unit file not found: /etc/systemd/system/$unit_name"
        info "Available unit files:"
        ls -la /etc/systemd/system/owui-*.service 2>/dev/null || warn "No owui service units found"
    fi
}

# Detect service type based on files present
detect_service_type() {
    local service_dir="$1"
    local full_path="$SUITE_DIR/$service_dir"
    
    if [ -f "$full_path/package.json" ]; then
        echo "nodejs"
    elif [ -f "$full_path/start.py" ]; then
        # Check if start.py uses uvicorn for FastAPI
        if grep -q "uvicorn\|fastapi" "$full_path/start.py" 2>/dev/null; then
            echo "python"  # Use start.py directly for FastAPI apps
        else
            echo "python"
        fi
    elif [ -f "$full_path/src/server.py" ]; then
        echo "fastapi"  # Only for services that have src/server.py specifically
    elif [ -f "$full_path/src/worker.py" ]; then
        echo "worker"
    elif [ -f "$full_path/src/app.py" ] && [ ! -f "$full_path/start.py" ]; then
        echo "fastapi"  # Only if no start.py exists
    elif [ -f "$full_path/start.sh" ]; then
        echo "shell"
    else
        echo "unknown"
    fi
}

# Create Node.js service unit
create_nodejs_unit() {
    local service_dir="$1"
    local service_path="$2"
    local unit_file="$3"
    
    sudo tee "$unit_file" >/dev/null <<UNITFILE
[Unit]
Description=OpenWebUI ${service_dir} (Node.js)
After=network.target
Wants=network.target

[Service]
Type=simple
User=owui
Group=owui
WorkingDirectory=$service_path
ExecStartPre=/bin/bash -c 'cd $service_path && [ ! -d node_modules ] && npm install || true'
ExecStart=/bin/bash $service_path/start.sh
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=5173

[Install]
WantedBy=multi-user.target
UNITFILE
}

# Create FastAPI service unit
create_fastapi_unit() {
    local service_dir="$1"
    local service_path="$2"
    local unit_file="$3"
    
    IFS=':' read -r port description <<< "${SERVICES[$service_dir]}"
    
    # Determine the correct module path for uvicorn
    local uvicorn_module="src.server:app"
    if [ -f "$service_path/src/app.py" ] && [ ! -f "$service_path/src/server.py" ]; then
        uvicorn_module="src.app:app"
    fi
    
    local env_vars=""
    case "$service_dir" in
        "00-pipelines-gateway")
            env_vars="Environment=GATEWAY_DB=$service_path/data/gateway.db"
            ;;
        "02-memory-2.0")
            env_vars="Environment=MEMORY_DB=$service_path/data/memory.db"
            ;;
        "13-policy-guardrails")
            env_vars="Environment=POLICY_DB=$service_path/data/policy.db"
            ;;
        "14-telemetry-cache")
            env_vars="Environment=TELEMETRY_DB=$service_path/data/telemetry.db"
            ;;
    esac
    
    sudo tee "$unit_file" >/dev/null <<UNITFILE
[Unit]
Description=OpenWebUI ${service_dir} (FastAPI)
After=network.target
Wants=network.target

[Service]
Type=simple
User=owui
Group=owui
WorkingDirectory=$service_path
EnvironmentFile=$ENV_FILE
$env_vars
Environment=PYTHONPATH=$service_path
Environment=PYTHONUNBUFFERED=1
ExecStart=$UVICORN_BIN $uvicorn_module --host 0.0.0.0 --port $port
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNITFILE
}

# Create worker service unit
create_worker_unit() {
    local service_dir="$1"
    local service_path="$2"
    local unit_file="$3"
    
    sudo tee "$unit_file" >/dev/null <<UNITFILE
[Unit]
Description=OpenWebUI ${service_dir} (Worker)
After=network.target
Wants=network.target

[Service]
Type=simple
User=owui
Group=owui
WorkingDirectory=$service_path
EnvironmentFile=$ENV_FILE
Environment=PYTHONPATH=$service_path
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 src/worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNITFILE
}

# Create Python service unit
create_python_unit() {
    local service_dir="$1"
    local service_path="$2" 
    local unit_file="$3"
    
    sudo tee "$unit_file" >/dev/null <<UNITFILE
[Unit]
Description=OpenWebUI ${service_dir} (Python)
After=network.target
Wants=network.target

[Service]
Type=simple
User=owui
Group=owui
WorkingDirectory=$service_path
EnvironmentFile=$ENV_FILE
Environment=PYTHONPATH=$service_path
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNITFILE
}

# Create shell service unit
create_shell_unit() {
    local service_dir="$1"
    local service_path="$2"
    local unit_file="$3"
    
    sudo tee "$unit_file" >/dev/null <<UNITFILE
[Unit]
Description=OpenWebUI ${service_dir} (Shell)
After=network.target
Wants=network.target

[Service]
Type=simple
User=owui
Group=owui
WorkingDirectory=$service_path
EnvironmentFile=$ENV_FILE
ExecStart=/bin/bash start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNITFILE
}

# Create systemd unit file for a service
create_service_unit() {
    local service_dir="$1"
    IFS=':' read -r port description <<< "${SERVICES[$service_dir]}"
    local unit_name="owui-${service_dir}.service"
    local unit_file="/etc/systemd/system/$unit_name"
    local service_path="$SUITE_DIR/$service_dir"
    
    say "Creating systemd unit for $service_dir..."
    
    # Check if service directory exists
    if [ ! -d "$service_path" ]; then
        err "Service directory not found: $service_path"
        return 1
    fi
    
    # Detect service type
    local service_type=$(detect_service_type "$service_dir")
    info "Detected service type: $service_type for $service_dir"
    
    # Create data directory for services that need it
    if [[ "$service_dir" =~ (gateway|memory|policy|telemetry) ]]; then
        sudo mkdir -p "$service_path/data"
        sudo chown -R owui:owui "$service_path/data"
        sudo chmod 755 "$service_path/data"
    fi
    
    # Create the systemd unit based on service type
    case "$service_type" in
        "nodejs")
            create_nodejs_unit "$service_dir" "$service_path" "$unit_file"
            ;;
        "fastapi")
            create_fastapi_unit "$service_dir" "$service_path" "$unit_file"
            ;;
        "worker")
            create_worker_unit "$service_dir" "$service_path" "$unit_file"
            ;;
        "python")
            create_python_unit "$service_dir" "$service_path" "$unit_file"
            ;;
        "shell")
            create_shell_unit "$service_dir" "$service_path" "$unit_file"
            ;;
        *)
            # Fallback to original logic for special cases
            if [ "$port" = "0" ]; then
                create_worker_unit "$service_dir" "$service_path" "$unit_file"
            else
                create_fastapi_unit "$service_dir" "$service_path" "$unit_file"
            fi
            ;;
    esac
    
    # Validate unit file was created successfully
    if [ ! -f "$unit_file" ]; then
        err "Failed to create unit file: $unit_file"
        return 1
    fi
    
    # Validate unit file syntax
    if ! sudo systemd-analyze verify "$unit_file" 2>/dev/null; then
        warn "Unit file syntax issues detected:"
        sudo systemd-analyze verify "$unit_file" 2>&1 || true
        return 1
    fi
    
    sudo systemctl daemon-reload
    
    # Verify unit is recognized by systemd
    if ! sudo systemctl cat "$unit_name" >/dev/null 2>&1; then
        err "Unit file not recognized by systemd: $unit_name"
        info "Unit file contents:"
        sudo cat "$unit_file"
        return 1
    fi
    
    ok "Created and validated unit file: $unit_file"
}
}

# Start a service
start_service() {
    local service_dir="$1"
    local unit_name="owui-${service_dir}.service"
    
    say "Starting $service_dir..."
    
    sudo systemctl enable "$unit_name"
    sudo systemctl start "$unit_name"
    sleep 2
    
    if systemctl is-active --quiet "$unit_name"; then
        ok "$service_dir is running"
    else
        err "$service_dir failed to start"
        show_service_logs "$service_dir" 10
        return 1
    fi
}

# Health check for a service
health_check() {
    local service_dir="$1"
    IFS=':' read -r port description <<< "${SERVICES[$service_dir]}"
    
    # Skip health check for worker daemon
    if [ "$port" = "0" ]; then
        if systemctl is-active --quiet "owui-${service_dir}.service"; then
            ok "$service_dir (worker): Running"
        else
            err "$service_dir (worker): Not running"
        fi
        return
    fi
    
    # Try different health endpoints
    local endpoints=("/healthz" "/health" "/")
    local healthy=false
    
    for endpoint in "${endpoints[@]}"; do
        if curl -fsS --connect-timeout 2 "http://127.0.0.1:${port}${endpoint}" >/dev/null 2>&1; then
            ok "$service_dir (:$port): Healthy"
            healthy=true
            break
        fi
    done
    
    if [ "$healthy" = false ]; then
        err "$service_dir (:$port): Not responding"
        # Check if port is listening
        if ss -lntp | grep -q ":${port}\s"; then
            warn "Port $port is listening but not responding to HTTP"
        else
            warn "Port $port is not listening"
        fi
    fi
}

# Health check all services
health_check_all() {
    say "Running health checks on all services..."
    
    printf "%-25s %-8s %s\n" "SERVICE" "PORT" "HEALTH"
    printf "%-25s %-8s %s\n" "-------" "----" "------"
    
    for service_dir in "${!SERVICES[@]}"; do
        IFS=':' read -r port description <<< "${SERVICES[$service_dir]}"
        
        if [ ! -d "$SUITE_DIR/$service_dir" ]; then
            printf "%-25s %-8s %s\n" "$service_dir" "$port" "MISSING"
            continue
        fi
        
        if ! systemctl is-active --quiet "owui-${service_dir}.service"; then
            printf "%-25s %-8s %s\n" "$service_dir" "$port" "STOPPED"
            continue
        fi
        
        if [ "$port" = "0" ]; then
            printf "%-25s %-8s %s\n" "$service_dir" "worker" "RUNNING"
        else
            if curl -fsS --connect-timeout 2 "http://127.0.0.1:${port}/healthz" >/dev/null 2>&1; then
                printf "%-25s %-8s %s\n" "$service_dir" "$port" "HEALTHY"
            else
                printf "%-25s %-8s %s\n" "$service_dir" "$port" "UNHEALTHY"
            fi
        fi
    done
}

# Show service structure and detection info
show_service_info() {
    local service_dir="$1"
    local service_path="$SUITE_DIR/$service_dir"
    
    if [ ! -d "$service_path" ]; then
        err "Service directory not found: $service_path"
        return 1
    fi
    
    echo "🔍 Service Information: $service_dir"
    echo "📁 Path: $service_path"
    echo "🏷️  Type: $(detect_service_type "$service_dir")"
    echo ""
    echo "📋 File Structure:"
    if [ -f "$service_path/package.json" ]; then
        echo "  ✅ package.json (Node.js service)"
    fi
    if [ -f "$service_path/start.py" ]; then
        echo "  ✅ start.py (Python entry point)"
        if grep -q "uvicorn" "$service_path/start.py" 2>/dev/null; then
            echo "    → Contains uvicorn (FastAPI)"
        fi
    fi
    if [ -f "$service_path/src/server.py" ]; then
        echo "  ✅ src/server.py (FastAPI server)"
    fi
    if [ -f "$service_path/src/app.py" ]; then
        echo "  ✅ src/app.py (FastAPI app)"
    fi
    if [ -f "$service_path/src/worker.py" ]; then
        echo "  ✅ src/worker.py (Background worker)"
    fi
    if [ -f "$service_path/start.sh" ]; then
        echo "  ✅ start.sh (Shell script)"
    fi
    echo ""
    
    # Show current systemd unit if it exists
    local unit_file="/etc/systemd/system/owui-${service_dir}.service"
    if [ -f "$unit_file" ]; then
        echo "🔧 Current Systemd Unit:"
        echo "ExecStart line:"
        grep "ExecStart=" "$unit_file" || echo "  No ExecStart found"
    else
        echo "❌ No systemd unit file found"
    fi
}

# Verify and fix all systemd units
verify_all_units() {
    say "Verifying all systemd units..."
    
    local missing_units=()
    local failed_units=()
    
    for service_dir in "${!SERVICES[@]}"; do
        if [ ! -d "$SUITE_DIR/$service_dir" ]; then
            warn "Skipping $service_dir - service directory not found"
            continue
        fi
        
        local unit_name="owui-${service_dir}.service"
        local unit_file="/etc/systemd/system/$unit_name"
        
        # Check if unit file exists
        if [ ! -f "$unit_file" ]; then
            missing_units+=("$service_dir")
            warn "Missing unit file: $unit_file"
        else
            # Check if unit is valid
            if ! sudo systemd-analyze verify "$unit_file" 2>/dev/null; then
                failed_units+=("$service_dir")
                warn "Invalid unit file: $unit_file"
            else
                ok "Valid unit: $unit_name"
            fi
        fi
    done
    
    # Create missing units
    if [ ${#missing_units[@]} -gt 0 ]; then
        say "Creating ${#missing_units[@]} missing unit files..."
        for service_dir in "${missing_units[@]}"; do
            info "Creating unit for $service_dir"
            create_service_unit "$service_dir"
        done
    fi
    
    # Recreate failed units
    if [ ${#failed_units[@]} -gt 0 ]; then
        say "Recreating ${#failed_units[@]} invalid unit files..."
        for service_dir in "${failed_units[@]}"; do
            info "Recreating unit for $service_dir"
            sudo rm -f "/etc/systemd/system/owui-${service_dir}.service"
            create_service_unit "$service_dir"
        done
    fi
    
    # Final verification
    sudo systemctl daemon-reload
    
    say "Unit verification summary:"
    printf "%-25s %-12s %s\n" "SERVICE" "STATUS" "UNIT FILE"
    printf "%-25s %-12s %s\n" "-------" "------" "---------"
    
    for service_dir in "${!SERVICES[@]}"; do
        if [ ! -d "$SUITE_DIR/$service_dir" ]; then
            continue
        fi
        
        local unit_name="owui-${service_dir}.service"
        local unit_file="/etc/systemd/system/$unit_name"
        
        if [ -f "$unit_file" ] && sudo systemd-analyze verify "$unit_file" 2>/dev/null; then
            printf "%-25s %-12s %s\n" "$service_dir" "✅ VALID" "$unit_file"
        else
            printf "%-25s %-12s %s\n" "$service_dir" "❌ INVALID" "$unit_file"
        fi
    done
}

# Bring up all services
bring_up_all() {
    say "Bringing up all OpenWebUI Suite services..."
    
    for service_dir in "${!SERVICES[@]}"; do
        # Skip if service directory doesn't exist
        if [ ! -d "$SUITE_DIR/$service_dir" ]; then
            warn "Skipping $service_dir - directory not found"
            continue
        fi
        
        local unit_name="owui-${service_dir}.service"
        
        # Create unit if it doesn't exist
        if [ ! -f "/etc/systemd/system/$unit_name" ]; then
            info "Creating unit for $service_dir"
            create_service_unit "$service_dir"
        fi
        
        # Start service if not running
        if ! systemctl is-active --quiet "$unit_name"; then
            start_service "$service_dir"
        else
            ok "$service_dir already running"
        fi
    done
}

# Main script logic
main() {
    case "${1:-help}" in
        "discover"|"list"|"status")
            check_prerequisites
            discover_services
            ;;
        "logs")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 logs <service-name> [lines]"
                echo "Available services: ${!SERVICES[*]}"
                exit 1
            fi
            show_service_logs "$2" "${3:-50}"
            ;;
        "create-unit")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 create-unit <service-name>"
                echo "Available services: ${!SERVICES[*]}"
                exit 1
            fi
            check_prerequisites
            create_service_unit "$2"
            ;;
        "verify")
            check_prerequisites
            verify_all_units
            ;;
        "info")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 info <service-name>"
                echo "Available services: ${!SERVICES[*]}"
                exit 1
            fi
            show_service_info "$2"
            ;;
        "start")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 start <service-name>"
                echo "Available services: ${!SERVICES[*]}"
                exit 1
            fi
            start_service "$2"
            ;;
        "health")
            if [ -n "${2:-}" ]; then
                health_check "$2"
            else
                health_check_all
            fi
            ;;
        "bring-up"|"startup"|"deploy")
            check_prerequisites
            bring_up_all
            echo
            health_check_all
            ;;
        "help"|*)
            cat <<HELP
OpenWebUI Suite Service Management

Usage: $0 <command> [options]

Commands:
  discover          Show all services and their status
  logs <service>    Show recent logs for a specific service
  create-unit <service>  Create systemd unit for a service
  verify            Verify and fix all systemd units
  info <service>    Show detailed service structure and configuration
  start <service>   Start a specific service
  health [service]  Check health of all services or a specific one
  bring-up         Create units and start all services
  help             Show this help

Available services:
$(printf "  %s\n" "${!SERVICES[@]}" | sort)

Examples:
  $0 discover                    # List all services
  $0 logs 00-pipelines-gateway   # Show gateway logs
  $0 info 06-byof-tool-hub       # Show service structure and config
  $0 verify                      # Verify all systemd units
  $0 health                      # Check all service health
  $0 bring-up                    # Start everything
HELP
            ;;
    esac
}

main "$@"
