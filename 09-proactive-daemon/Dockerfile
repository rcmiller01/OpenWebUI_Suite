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

# This is a worker daemon, not a web service
ENV WORKER_MODULE="src.worker" \
    CONFIG_FILE="config/triggers.yaml" \
    VERBOSE="false" \
    ONCE="false"

# No exposed port for worker daemon

# Start the worker daemon directly
CMD ["python", "src/worker.py"]
