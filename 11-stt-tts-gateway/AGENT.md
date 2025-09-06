# 11-STT-TTS-Gateway Agent

## Overview

The STT-TTS Gateway provides local speech-to-text and text-to-speech capabilities for the OpenWebUI Suite. It integrates faster-whisper for high-performance speech recognition and Coqui TTS models for natural voice synthesis, with optional timestamp generation.

## Architecture

- **STT Engine**: faster-whisper (local, fast, accurate)
- **TTS Engine**: Coqui TTS (local, high-quality synthesis)
- **API**: FastAPI with async endpoints
- **Audio Processing**: WAV/MP3 support with automatic format detection
- **Deployment**: Single container or dual-container setup

## API Endpoints

### POST /stt

Speech-to-text conversion endpoint.

**Request:**

```json
{
  "audio": "base64_encoded_audio_data",
  "format": "wav|mp3|flac",
  "language": "en|auto",
  "timestamps": true
}
```

**Response:**

```json
{
  "text": "Transcribed text content",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello world"
    }
  ],
  "language": "en",
  "processing_time": 0.234
}
```

### POST /tts

Text-to-speech synthesis endpoint.

**Request:**

```json
{
  "text": "Text to synthesize",
  "voice": "default",
  "speed": 1.0,
  "timestamps": true
}
```

**Response:**

```json
{
  "audio_url": "/audio/generated_12345.wav",
  "timestamps": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.5
    },
    {
      "word": "world",
      "start": 0.5,
      "end": 1.0
    }
  ],
  "duration": 1.2,
  "processing_time": 0.456
}
```

### GET /audio/{filename}

Retrieve generated audio files.

**Response:** Audio file stream

## Configuration

### Environment Variables

```bash
# Core Configuration
STT_MODEL_SIZE=tiny|base|small|medium|large        # Whisper size passed to faster-whisper
TTS_MODEL_NAME=tts_models/en/ljspeech/tacotron2-DDC_ph  # Coqui TTS model id
AUDIO_STORAGE_PATH=/app/audio
MAX_AUDIO_SIZE_MB=50
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Optional build-time prefetch (Docker ARG PREFETCH_MODELS=true)
PREFETCH_MODELS=true
```

### Docker Configuration

```yaml
# Single container setup
services:
  stt-tts-gateway:
    build: .
    ports:
      - "8089:8089"
    volumes:
      - ./audio:/app/audio
    environment:
      - STT_MODEL_SIZE=base
      - CORS_ORIGINS=http://localhost:3000

# Dual container setup (advanced)
services:
  stt-service:
    # STT-specific container
  tts-service:
    # TTS-specific container
  gateway:
    # Orchestrator container
```

## Dependencies

Core (resolve via root constraints):

- faster-whisper
- torch / torchaudio
- TTS
- pydantic
- uvicorn
- python-multipart
- aiofiles

## Performance Requirements

- **STT Latency**: <500ms for 5-second audio clips
- **TTS Latency**: <1000ms for 100-word text
- **Memory Usage**: <2GB for base models
- **Concurrent Requests**: Support 10+ simultaneous conversions

## Development

### Local Setup (CPU)

```bash
# Install dependencies
pip install -r requirements.txt

# Download models
python - <<'PY'
from faster_whisper import WhisperModel
from TTS.api import TTS
WhisperModel('base', device='cpu', compute_type='int8')
TTS('tts_models/en/ljspeech/tacotron2-DDC_ph')
print('Prefetched models')
PY

# Run service
python src/app.py
```

### Testing

```bash
# Run API tests
python test_api.py

# Test STT performance
curl -X POST http://localhost:8089/stt \
  -F "audio=@test_audio.wav" \
  -F "timestamps=true"

# Test TTS
curl -X POST http://localhost:8089/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"default","timestamps":true}'
```

## Integration Points

- **OpenWebUI Frontend**: CORS-enabled for direct browser access
- **Pipelines Gateway**: Audio processing pipeline integration
- **Multimodal Router**: Audio stream routing
- **Drive State**: Voice command processing

## Error Handling

- Invalid audio format → 400 Bad Request
- Model loading failure → 503 Service Unavailable
- Processing timeout → 504 Gateway Timeout
- Storage full → 507 Insufficient Storage

## Monitoring & Health

- Health endpoints: `/health` (detailed), `/healthz` (lightweight)
- Logs include processing timings
- Background cleanup thread removes expired audio

## Security Considerations

- Input validation for audio file sizes
- Rate limiting for API endpoints
- Temporary file cleanup
- No persistent storage of audio data
- CORS configuration for authorized origins only

## Future Enhancements

- Streaming STT (chunked websockets)
- Advanced timestamp alignment
- Voice cloning / speaker embedding
- Multi-language dynamic model switching
- GPU acceleration (CUDA image variant `-cuda`)
