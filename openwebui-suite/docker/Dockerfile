# Multi-stage Dockerfile for OpenWebUI Suite
# Builds a composite image with core + plugins

ARG CORE_VERSION=v1.0.0-robert.1
ARG PYTHON_VERSION=3.11

# =============================================================================
# Base stage: Core OpenWebUI image
# =============================================================================
FROM ghcr.io/<ORG>/openwebui-core:${CORE_VERSION} as core

# =============================================================================
# Plugin stage: Install Python plugins
# =============================================================================
FROM python:${PYTHON_VERSION}-slim as plugin-installer

# Install system dependencies for building wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for plugins
RUN python -m venv /opt/plugins
ENV PATH="/opt/plugins/bin:$PATH"

# Install plugin dependencies
COPY requirements-plugins.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-plugins.txt

# Install plugins
ARG PLUGIN_VERSIONS="owui-plugin-ollama-tools==0.1.0"
RUN pip install --no-cache-dir ${PLUGIN_VERSIONS}

# =============================================================================
# Widget stage: Build frontend widgets  
# =============================================================================
FROM node:18-alpine as widget-builder

WORKDIR /widgets

# Copy widget package files
COPY package-widgets.json package.json
COPY package-widgets-lock.json package-lock.json

# Install widget dependencies
RUN npm ci --only=production

# Build widgets (if needed)
RUN npm run build 2>/dev/null || echo "No build script found"

# =============================================================================
# Final stage: Combine everything
# =============================================================================
FROM core

# Set labels
LABEL org.opencontainers.image.title="OpenWebUI Suite"
LABEL org.opencontainers.image.description="OpenWebUI with plugin system and extensions"
LABEL org.opencontainers.image.vendor="OpenWebUI Suite"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="2025.09.03"

# Install Python (if not already in core)
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Copy plugin virtual environment
COPY --from=plugin-installer /opt/plugins /opt/plugins

# Copy widgets
COPY --from=widget-builder /widgets/dist /app/web/extensions/widgets/

# Create data directory
RUN mkdir -p /data /config && \
    chown -R 1000:1000 /data /config

# Environment variables
ENV PYTHONPATH="/opt/plugins/lib/python3.11/site-packages:$PYTHONPATH"
ENV PATH="/opt/plugins/bin:$PATH"
ENV OWUI_MEMORY_PATH="/data/memory.sqlite"
ENV OWUI_PLUGIN_TIMEOUT="30"
ENV OWUI_WIDGET_CACHE_TTL="3600"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Switch back to app user
USER 1000

# Expose ports
EXPOSE 3000

# Volume mounts
VOLUME ["/data", "/config"]

# Default command (inherited from core image)
# CMD ["python", "-m", "backend.main"]
