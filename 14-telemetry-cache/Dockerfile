ARG BASE_IMAGE=owui/base:py311
FROM ${BASE_IMAGE} as runtime
WORKDIR /app
ENV TELEMETRY_CACHE_VERSION=1.0.0 \
        REDIS_URL=redis://redis:6379 \
        PROMETHEUS_PORT=9090 \
        LOG_LEVEL=INFO
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt -c /app/constraints.txt
COPY src ./src
COPY start.py .
COPY start.sh .
RUN chmod +x start.sh start.py
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys;\nurl='http://localhost:8000/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=3).read();\nexcept Exception:\n sys.exit(1)" || exit 1
CMD ["python", "start.py"]
