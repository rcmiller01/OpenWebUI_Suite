# FastVLM Sidecar Agent

## Goal
Run Apple's FastVLM locally to generate fast, privacy-friendly vision observations for images (and optionally frames pulled from short videos). Output is normalized to your pipeline schema:

```json
{ "observations": [{ "label": "scene", "text": "..." }], "safety": [] }
```

## Why
Use FastVLM as the local first pass; escalate to remote VLMs (OpenRouter) only when the intent router marks low confidence or the user explicitly asks for high-fidelity analysis.

## API

### POST /analyze
Analyze an image and return structured observations.

**Request Body:**
```json
{
  "image_url": "http(s)://...",
  "image_b64": "...",
  "prompt": "optional override",
  "max_new_tokens": 192
}
```

**Response:**
```json
{
  "observations": [{ "label": "scene", "text": "bullet points / concise text" }],
  "safety": []
}
```

### GET /healthz
Health check endpoint.

**Response:**
```json
{"ok": true}
```

## Model & ENV

Default: `apple/fastvlm-2.7b` (good speed/VRAM).

**Environment Variables:**
- `FASTVLM_MODEL=apple/fastvlm-2.7b`
- `DEVICE=cuda` (or "cpu" for slower processing)
- `TORCH_DTYPE=float16` (or "float32" on CPU)
- `MAX_TOKENS=192`

## Deployment

### GPU Deployment (Recommended)
```bash
docker build -t fastvlm-sidecar:latest 16-fastvlm-sidecar
docker run --gpus all -p 8115:8115 --env FASTVLM_MODEL=apple/fastvlm-2.7b fastvlm-sidecar:latest
```

### CPU Deployment
```bash
docker run --env DEVICE=cpu --env TORCH_DTYPE=float32 -p 8115:8115 fastvlm-sidecar:latest
```

## Testing

### Health Check
```bash
curl http://localhost:8115/healthz
```

### Image Analysis
```bash
curl -X POST http://localhost:8115/analyze \
  -H 'content-type: application/json' \
  -d '{"image_url":"https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg"}'
```

## Integration

The FastVLM sidecar is registered in the pipelines gateway service registry:

```json
{
  "fastvlm": "http://localhost:8115"
}
```

It works as a fallback chain: FastVLM → Multimodal Router → Skip (if both fail).

## Performance

- **FastVLM 2.7B**: ~1-2 seconds per image on modern GPU
- **Memory Usage**: ~4-6GB VRAM for CUDA, ~8GB RAM for CPU
- **Output**: Concise bullet points, optimized for pipeline injection
