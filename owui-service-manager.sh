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
    
    if systemctl list-units --all | grep -q "$unit_name"; then
        journalctl -u "$unit_name" -n "$lines" --no-pager || warn "No logs available for $unit_name"
    else
        warn "Systemd unit $unit_name not found"
    fi
}

# Create systemd unit for a service
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
    
    # Create data directory for services that need it
    if [[ "$service_dir" =~ (gateway|memory|policy|telemetry) ]]; then
        sudo mkdir -p "$service_path/data"
        sudo chown -R root:root "$service_path/data"
        sudo chmod 755 "$service_path/data"
    fi
    
    # Special handling for worker daemon (no port)
    if [ "$port" = "0" ]; then
        sudo tee "$unit_file" >/dev/null <<UNITFILE
[Unit]
Description=$description
After=network-online.target
Wants=network-online.target

[Service]
User=root
WorkingDirectory=$service_path
EnvironmentFile=$ENV_FILE
ExecStart=/usr/bin/python3 src/worker.py
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
UNITFILE
    else
        # Standard HTTP service
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
Description=$description
After=network-online.target
Wants=network-online.target

[Service]
User=root
WorkingDirectory=$service_path
EnvironmentFile=$ENV_FILE
$env_vars
ExecStart=$UVICORN_BIN src.server:app --host 0.0.0.0 --port $port
Restart=always
RestartSec=2
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
UNITFILE
    fi
    
    sudo systemctl daemon-reload
    ok "Created unit file: $unit_file"
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
  start <service>   Start a specific service
  health [service]  Check health of all services or a specific one
  bring-up         Create units and start all services
  help             Show this help

Available services:
$(printf "  %s\n" "${!SERVICES[@]}" | sort)

Examples:
  $0 discover                    # List all services
  $0 logs 00-pipelines-gateway   # Show gateway logs
  $0 health                      # Check all service health
  $0 bring-up                    # Start everything
HELP
            ;;
    esac
}

main "$@"
