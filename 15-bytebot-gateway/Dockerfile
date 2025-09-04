# Dockerfile for ByteBot Gateway
FROM python:3.11-slim

LABEL org.opencontainers.image.title="ByteBot Gateway"
LABEL org.opencontainers.image.description="Secure desktop automation gateway for OpenWebUI Pipelines"
LABEL org.opencontainers.image.version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8089

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8089/health || exit 1

# Set default environment variables
ENV HOST=0.0.0.0
ENV PORT=8089
ENV LOG_LEVEL=INFO

# Start the application
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8089"]
