#!/bin/bash
# freeze.sh - Freeze current plugin versions and create a new release manifest

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
MANIFESTS_DIR="$REPO_ROOT/manifests"
CURRENT_DATE=$(date +%Y.%m.%d)
MANIFEST_FILE="$MANIFESTS_DIR/release-$CURRENT_DATE.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to get the latest version of a package from PyPI
get_pypi_version() {
    local package_name="$1"
    curl -s "https://pypi.org/pypi/$package_name/json" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['info']['version'])" 2>/dev/null || echo "unknown"
}

# Function to get the latest version of an npm package
get_npm_version() {
    local package_name="$1"
    local registry="${2:-https://registry.npmjs.org}"
    curl -s "$registry/$package_name" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['dist-tags']['latest'])" 2>/dev/null || echo "unknown"
}

# Function to check if a git tag exists
check_git_tag() {
    local repo="$1"
    local tag="$2"
    git ls-remote --tags "https://github.com/$repo" | grep -q "refs/tags/$tag" || return 1
}

# Function to get the latest git tag
get_latest_git_tag() {
    local repo="$1"
    git ls-remote --tags "https://github.com/$repo" | \
        grep -o 'refs/tags/v[0-9]*\.[0-9]*\.[0-9]*' | \
        sed 's|refs/tags/||' | \
        sort -V | \
        tail -1 || echo "unknown"
}

# Main function
main() {
    log_info "Starting release freeze process for $CURRENT_DATE"
    
    # Check if manifest already exists
    if [[ -f "$MANIFEST_FILE" ]]; then
        log_warn "Manifest file already exists: $MANIFEST_FILE"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Aborting"
            exit 0
        fi
    fi
    
    # Create manifests directory if it doesn't exist
    mkdir -p "$MANIFESTS_DIR"
    
    log_info "Gathering current plugin versions..."
    
    # Get plugin versions
    local template_version=$(get_pypi_version "owui-plugin-template")
    local ollama_tools_version=$(get_pypi_version "owui-plugin-ollama-tools")
    
    # Get widget versions
    local widget_template_version=$(get_npm_version "@openwebui-suite/owui-widget-template" "https://npm.pkg.github.com")
    
    # Get core version (assuming it follows a tag pattern)
    local core_version=$(get_latest_git_tag "<ORG>/openwebui-core")
    
    log_info "Found versions:"
    log_info "  Core: $core_version"
    log_info "  Plugin Template: $template_version"
    log_info "  Ollama Tools: $ollama_tools_version"
    log_info "  Widget Template: $widget_template_version"
    
    # Generate the manifest
    log_info "Generating manifest: $MANIFEST_FILE"
    
    cat > "$MANIFEST_FILE" << EOF
# OpenWebUI Suite Release Manifest
# Date: $CURRENT_DATE
# This manifest pins the versions of all components in the suite

metadata:
  version: "$CURRENT_DATE"
  description: "OpenWebUI Suite release $(date +%B\ %d,\ %Y)"
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  compatibility:
    openwebui_core: ">=1.0.0"
    python: ">=3.10"

# Core OpenWebUI fork with extension system
core:
  repository: "ghcr.io/<ORG>/openwebui-core"
  tag: "$core_version"
  digest: "sha256:placeholder-core-digest"
  features:
    - "backend-extension-loader"
    - "frontend-widget-loader"
    - "admin-plugin-panel"

# Python plugins to be installed
plugins:
  - name: "owui-plugin-template"
    version: "$template_version"
    source: "pypi"
    registry: "https://pypi.org/simple/"
    package: "owui-plugin-template"
    entry_point: "openwebui.plugins"
    required: false
    description: "Template plugin for development reference"
    
  - name: "owui-plugin-ollama-tools"
    version: "$ollama_tools_version"
    source: "pypi"
    registry: "https://pypi.org/simple/"
    package: "owui-plugin-ollama-tools"
    entry_point: "openwebui.plugins"
    required: true
    description: "Ollama integration tools and utilities"
    environment:
      - "OLLAMA_HOST"
      - "OWUI_MEMORY_PATH"

# Frontend widgets to be included
widgets:
  - name: "owui-widget-template"
    version: "$widget_template_version"
    source: "npm"
    registry: "https://npm.pkg.github.com"
    package: "@<ORG>/owui-widget-template"
    required: false
    description: "Template widget for development reference"

# Environment variable defaults
environment:
  defaults:
    OLLAMA_HOST: "http://core2-gpu:11434"
    OWUI_MEMORY_PATH: "/data/memory.sqlite"
    OWUI_PLUGIN_TIMEOUT: "30"
    OWUI_WIDGET_CACHE_TTL: "3600"
  
  required:
    - "OLLAMA_HOST"
  
  optional:
    - "OWUI_MEMORY_PATH"
    - "OWUI_PLUGIN_TIMEOUT"
    - "OWUI_WIDGET_CACHE_TTL"

# Health check configuration
healthcheck:
  interval: "30s"
  timeout: "10s"
  retries: 3
  start_period: "60s"
  endpoints:
    - "/health"
    - "/ext/ollama/health"
    - "/ext/template/health"

# Build configuration
build:
  base_image: "python:3.11-slim"
  build_args:
    CORE_VERSION: "$core_version"
    PLUGIN_VERSIONS: "owui-plugin-ollama-tools==$ollama_tools_version"
  
  labels:
    org.opencontainers.image.title: "OpenWebUI Suite"
    org.opencontainers.image.description: "OpenWebUI with plugin system"
    org.opencontainers.image.version: "$CURRENT_DATE"
    org.opencontainers.image.vendor: "OpenWebUI Suite"
    org.opencontainers.image.licenses: "MIT"

# CI/CD configuration
ci:
  triggers:
    - "manifest_change"
    - "core_release"
    - "plugin_release"
  
  build_matrix:
    platforms:
      - "linux/amd64"
      - "linux/arm64"
  
  tests:
    - "health_check"
    - "plugin_load"
    - "api_smoke_test"
  
  publish:
    registry: "ghcr.io"
    repository: "<ORG>/openwebui-suite"
    tags:
      - "$CURRENT_DATE"
      - "latest"
EOF
    
    log_success "Manifest generated successfully!"
    log_info "Next steps:"
    log_info "  1. Review the manifest file: $MANIFEST_FILE"
    log_info "  2. Commit and push to trigger CI/CD build"
    log_info "  3. Tag the release: git tag $CURRENT_DATE"
    log_info "  4. Test the deployment: docker compose up"
    
    # Generate requirements files for Docker build
    log_info "Generating requirements files..."
    
    cat > "$REPO_ROOT/docker/requirements-plugins.txt" << EOF
# Generated by freeze.sh on $(date)
owui-plugin-template==$template_version
owui-plugin-ollama-tools==$ollama_tools_version
EOF
    
    cat > "$REPO_ROOT/docker/package-widgets.json" << EOF
{
  "name": "openwebui-suite-widgets",
  "version": "$CURRENT_DATE",
  "private": true,
  "dependencies": {
    "@<ORG>/owui-widget-template": "$widget_template_version"
  }
}
EOF
    
    log_success "Requirements files generated in docker/ directory"
    log_info "Freeze process completed!"
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    command -v curl >/dev/null 2>&1 || missing_deps+=("curl")
    command -v python3 >/dev/null 2>&1 || missing_deps+=("python3")
    command -v git >/dev/null 2>&1 || missing_deps+=("git")
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and try again"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    check_dependencies
    main "$@"
fi
