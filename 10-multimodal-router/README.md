# Multimodal Router Service

A FastAPI service that provides multimodal analysis capabilities (image and audio) for the OpenWebUI Suite pipelines gateway.

## Features

- **Image Analysis**: Analyze images via Vision Language Models (VLMs) on OpenRouter
- **Audio Analysis**: Transcribe and summarize audio using local STT or remote models
- **Flexible Routing**: Support for both local and remote processing
- **Normalized Output**: Consistent observation format for easy integration
- **Health Monitoring**: Built-in health check endpoint

## Quick Start

### 1. Environment Setup

```bash
# Required
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional (with defaults)
export VISION_MODEL="openai/gpt-4o-mini"
export AUDIO_MODEL="openai/gpt-4o-mini"
export STT_URL="http://stt-tts:8111/stt"
export PROMPT_IMAGE="Describe the image focusing on diagrams, text, and safety."
export PROMPT_AUDIO="Transcribe verbatim, then summarize in three bullet points."
```

### 2. Run Locally

```bash
cd 10-multimodal-router
pip install -r requirements.txt
python -m uvicorn src.app:app --host 0.0.0.0 --port 8110
```

### 3. Run with Docker

```bash
docker build -t multimodal-router .
docker run -p 8110:8110 -e OPENROUTER_API_KEY=your-key multimodal-router
```

## API Endpoints

### POST `/mm/image`
Analyze an image and return structured observations.

**Request Body:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "image_b64": "base64-encoded-image-data",
  "prompt": "Custom analysis prompt (optional)"
}
```

**Response:**
```json
{
  "observations": [
    {
      "label": "scene",
      "text": "Analysis result text..."
    }
  ],
  "safety": []
}
```

### POST `/mm/audio`
Analyze audio with transcription and summarization.

**Request Body (Form Data):**
- `file`: Audio file (WAV, MP3, etc.)
- `prompt`: Custom prompt (optional)
- `prefer_remote`: Use remote audio model if available (default: false)

**Response:**
```json
{
  "transcript": "Full audio transcription...",
  "observations": [
    {
      "label": "summary",
      "text": "Summarized key points..."
    }
  ]
}
```

### GET `/healthz`
Health check endpoint.

**Response:**
```json
{"ok": true}
```

## Integration with Pipelines Gateway

The multimodal router is already configured in the pipelines gateway service registry:

```json
{
  "multimodal": "http://localhost:8110"
}
```

### Usage in Pipeline Processing

In your gateway's pre/mid processing hooks, detect multimodal intents and call these endpoints:

```python
# Example: Image analysis integration
if intent == "mm_image":
    image_data = extract_image_from_message(message)
    result = await S["multimodal"].post("/mm/image", image_data)
    # Inject observations into context
    ctx["observations"] = result["observations"]
```

## Testing

### Health Check
```bash
curl http://localhost:8110/healthz
```

### Image Analysis (URL)
```bash
curl -X POST http://localhost:8110/mm/image \
  -H 'Content-Type: application/json' \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "prompt": "Describe the scene briefly."
  }'
```

### Image Analysis (Base64)
```bash
b64=$(base64 -w0 image.jpg)
curl -X POST http://localhost:8110/mm/image \
  -H 'Content-Type: application/json' \
  -d "{\"image_b64\": \"$b64\"}"
```

### Audio Analysis
```bash
curl -X POST http://localhost:8110/mm/audio \
  -F 'file=@audio.wav' \
  -F 'prompt=Transcribe and summarize key points.'
```

## Architecture

### Image Processing Flow
1. Receive image (URL or base64)
2. Route to OpenRouter VLM with custom prompt
3. Return normalized observation format
4. Handle errors gracefully

### Audio Processing Flow
1. Receive audio file
2. Option 1: Direct remote audio model (if supported)
3. Option 2: Local STT → OpenRouter summarization
4. Return transcript + observations

### Error Handling
- Missing API keys → 500 error
- Invalid image/audio → 400 error
- OpenRouter failures → Fallback to local processing (audio)
- Network timeouts → Configurable retry logic

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Required | OpenRouter API key |
| `VISION_MODEL` | `openai/gpt-4o-mini` | Model for image analysis |
| `AUDIO_MODEL` | `openai/gpt-4o-mini` | Model for direct audio processing |
| `STT_URL` | `http://stt-tts:8111/stt` | Local STT service URL |
| `PROMPT_IMAGE` | Built-in prompt | Default image analysis prompt |
| `PROMPT_AUDIO` | Built-in prompt | Default audio analysis prompt |

## Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `httpx`: Async HTTP client
- `pydantic`: Data validation
- `python-multipart`: File upload handling

## Port Configuration

- **Service Port**: 8110
- **Health Check**: `GET /healthz`
- **Image Analysis**: `POST /mm/image`
- **Audio Analysis**: `POST /mm/audio`
