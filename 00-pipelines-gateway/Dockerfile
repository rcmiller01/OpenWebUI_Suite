ARG BASE_IMAGE=owui/base:py311
FROM ${BASE_IMAGE} AS runtime

LABEL org.opencontainers.image.title="OpenWebUI Pipelines Gateway"
LABEL org.opencontainers.image.description="OpenAI-compatible chat completions with plugin hooks"
LABEL org.opencontainers.image.version="1.0.0"

# Set working directory
WORKDIR /app

# Copy service requirements & install with global constraints
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt -c /app/constraints.txt

# Copy application code (after deps for layer cache)
COPY . .

# Expose port
EXPOSE 8088

# Health check (align with /healthz for quick probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys;\nurl='http://localhost:8088/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=3).read();\nexcept Exception:\n sys.exit(1)" || exit 1

# Set default environment variables
ENV HOST=0.0.0.0
ENV PORT=8088
ENV LOG_LEVEL=INFO

# Start the application
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8088"]
