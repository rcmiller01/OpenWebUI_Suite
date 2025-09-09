# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OS deps (curl for health checks/debug; build-base only if you have native wheels to compile)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only deps first for layer caching (adapt to your service)
# If you use requirements.txt:
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# If you use pyproject.toml:
# COPY pyproject.toml poetry.lock* ./
# RUN pip install --upgrade pip && pip install --no-cache-dir .

# Then copy the service code
COPY . /app

# Install runtime deps (gunicorn/uvicorn). If already in requirements, skip.
RUN pip install --no-cache-dir gunicorn uvicorn fastapi || true

# These can be overridden by env at runtime
ENV SERVICE_MODULE="app.main:app" \
    SERVICE_PORT="8000" \
    WORKERS="2" \
    TIMEOUT="60"

EXPOSE 8000

# Gunicorn + Uvicorn worker (sane defaults; env overrides allowed)
CMD ["sh", "-c", "exec gunicorn -k uvicorn.workers.UvicornWorker ${SERVICE_MODULE} -w ${WORKERS} -b 0.0.0.0:${SERVICE_PORT} --timeout ${TIMEOUT}"]
