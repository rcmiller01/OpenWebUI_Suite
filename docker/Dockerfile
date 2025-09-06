ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

LABEL org.opencontainers.image.title="OWUI Base Image" \
      org.opencontainers.image.description="Shared base for OpenWebUI Suite services" \
      org.opencontainers.image.source="https://github.com/rcmiller01/OpenWebUI_Suite"

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=off PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_CACHE_DIR=/app/.pip-cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git wget ca-certificates ffmpeg libsndfile1 libgl1 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 owui && mkdir -p /app && chown owui /app
WORKDIR /app
USER owui

COPY constraints.txt /app/constraints.txt

ENTRYPOINT ["python","-c","print('OWUI base ready')"]
