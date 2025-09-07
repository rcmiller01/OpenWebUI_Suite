#!/usr/bin/env bash
set -Eeuo pipefail

# OpenWebUI Suite Sanity Checker
# Verifies compose config, DNS resolution, and HTTP health endpoints

C="-f /root/compose.prod.yml"
NET="${NET:-root_owui}"
IMG="curlimages/curl:8.9.1"

echo "🔍 OpenWebUI Suite Sanity Check"
echo "==============================="

echo
echo "== Compose Configuration =="
if docker compose $C config -q; then
    echo "✅ Compose file valid"
else
    echo "❌ Compose file invalid"
    exit 1
fi

echo
echo "== Service Status =="
docker compose $C ps || true

echo
echo "== DNS Resolution =="
for h in gateway policy telemetry; do
    if docker run --rm --network "$NET" busybox:1.36 nslookup "$h" >/dev/null 2>&1; then
        echo "🔎 $h dns ok"
    else
        echo "❌ $h dns failed"
    fi
done

echo
echo "== HTTP Health Checks =="

# Gateway health check
if docker run --rm --network "$NET" $IMG -sS http://gateway:8000/health >/dev/null 2>&1; then
    echo "✅ gateway health ok"
elif docker run --rm --network "$NET" $IMG -sS http://gateway:8000/healthz >/dev/null 2>&1; then
    echo "✅ gateway healthz ok"
else
    echo "❌ gateway unreachable"
fi

# Policy service health check
if docker run --rm --network "$NET" $IMG -sS http://policy:8001/health >/dev/null 2>&1; then
    echo "✅ policy health ok"
elif docker run --rm --network "$NET" $IMG -sS http://policy:8001/healthz >/dev/null 2>&1; then
    echo "✅ policy healthz ok"
else
    echo "❌ policy unreachable"
fi

# Telemetry/Prometheus check
if docker run --rm --network "$NET" $IMG -sS http://telemetry:9090/-/ready >/dev/null 2>&1; then
    echo "✅ prometheus ready"
else
    echo "❌ prometheus not ready"
fi

# Optional additional checks for other services
echo
echo "== Additional Service Checks =="

# Intent router
if docker run --rm --network "$NET" $IMG -sS http://intent-router:8002/healthz >/dev/null 2>&1; then
    echo "✅ intent-router ok"
else
    echo "⚠️  intent-router not responding (may not be running)"
fi

# Memory service
if docker run --rm --network "$NET" $IMG -sS http://memory:8003/healthz >/dev/null 2>&1; then
    echo "✅ memory service ok"
else
    echo "⚠️  memory service not responding (may not be running)"
fi

# STT-TTS Gateway
if docker run --rm --network "$NET" $IMG -sS http://stt-tts:8089/healthz >/dev/null 2>&1; then
    echo "✅ stt-tts gateway ok"
else
    echo "⚠️  stt-tts gateway not responding (may not be running)"
fi

echo
echo "== Network Information =="
echo "Network: $NET"
echo "Compose file: $C"

echo
echo "🎯 Sanity check complete!"
echo
echo "Next steps:"
echo "- Check 'docker compose $C logs' for any service errors"
echo "- Visit http://localhost:8000 for gateway"
echo "- Visit http://localhost:9090 for Prometheus (if telemetry enabled)"
