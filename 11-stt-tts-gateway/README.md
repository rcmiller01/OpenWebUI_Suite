# 11-STT-TTS-Gateway

Local Speech-to-Text and Text-to-Speech service for the OpenWebUI Suite using faster-whisper and Coqui TTS.

## Features

- **Speech-to-Text**: High-performance transcription using faster-whisper
- **Text-to-Speech**: Natural voice synthesis with word-level timestamps
- **REST API**: FastAPI-based endpoints with CORS support
- **Audio Processing**: Support for WAV, MP3, and FLAC formats
- **Performance**: Optimized for low latency (<500ms STT, <1000ms TTS)
- **Container Ready**: Docker deployment with health checks

## Quick Start

### Using Docker Compose

```bash
# Clone and navigate to the service directory
cd 11-stt-tts-gateway

# Start the service
docker-compose up -d

# Check health
curl http://localhost:8089/health
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Download models (optional, will auto-download on first use)
python -c "import faster_whisper; faster_whisper.WhisperModel('base')"

# Start the service
python start.py

# Or use the shell script
./start.sh
```

## API Usage

### Speech-to-Text

```bash
# Convert audio file to text
curl -X POST http://localhost:8089/stt \
  -H "Content-Type: application/json" \
  -d '{
    "audio": "'$(base64 -w 0 audio.wav)'",
    "format": "wav",
    "language": "en",
    "timestamps": true
  }'
```

Response:
```json
{
  "text": "Hello world, this is a test.",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello world,"
    }
  ],
  "language": "en",
  "processing_time": 0.234
}
```

### Text-to-Speech

```bash
# Convert text to speech
curl -X POST http://localhost:8089/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world, this is a test.",
    "voice": "default",
    "speed": 1.0,
    "timestamps": true
  }'
```

Response:
```json
{
  "audio_url": "/audio/generated_abc123.wav",
  "timestamps": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.5
    }
  ],
  "duration": 2.1,
  "processing_time": 0.456
}
```

### Retrieve Audio

```bash
# Download generated audio
curl http://localhost:8089/audio/generated_abc123.wav -o output.wav
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_MODEL_SIZE` | `base` | Whisper model size (tiny, base, small, medium, large) |
| `TTS_MODEL_NAME` | `tts_models/en/ljspeech/tacotron2-DDC_ph` | TTS model to use |
| `AUDIO_STORAGE_PATH` | `./audio` | Directory for temporary audio files |
| `MAX_AUDIO_SIZE_MB` | `50` | Maximum audio file size in MB |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8080` | Allowed CORS origins |

### Docker Compose

```yaml
version: '3.8'
services:
  stt-tts-gateway:
    build: .
    ports:
      - "8089:8089"
    environment:
      - STT_MODEL_SIZE=base
      - CORS_ORIGINS=http://localhost:3000
    volumes:
      - ./audio:/app/audio
```

## Testing

```bash
# Run API tests
python test_api.py

# Manual testing with curl
./test_curl.sh
```

## Performance

- **STT**: <500ms for 5-second audio clips
- **TTS**: <1000ms for 100-word text
- **Memory**: ~2GB for base models
- **Concurrent**: Supports 10+ simultaneous requests

## Integration

### OpenWebUI Frontend

The service is designed to work with OpenWebUI frontend:

```javascript
// Example frontend integration
async function transcribeAudio(audioBlob) {
  const base64 = await blobToBase64(audioBlob);
  const response = await fetch('/api/stt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio: base64,
      format: 'wav',
      timestamps: true
    })
  });
  return response.json();
}
```

### Pipelines Integration

```python
# Example Pipelines integration
import requests

def process_audio_pipeline(audio_data):
    # Send to STT
    stt_response = requests.post('http://localhost:8089/stt', json={
        'audio': audio_data,
        'timestamps': True
    })

    # Process text...

    # Generate TTS response
    tts_response = requests.post('http://localhost:8089/tts', json={
        'text': 'Response text',
        'timestamps': True
    })

    return tts_response.json()
```

## Troubleshooting

### Common Issues

1. **Model loading failures**
   ```bash
   # Clear model cache
   rm -rf ~/.cache/whisper
   rm -rf ~/.cache/coqui
   ```

2. **Memory issues**
   ```bash
   # Use smaller models
   export STT_MODEL_SIZE=tiny
   ```

3. **Audio format errors**
   ```bash
   # Convert audio to supported format
   ffmpeg -i input.mp3 -acodec pcm_s16le -ar 16000 output.wav
   ```

### Logs

```bash
# View service logs
docker-compose logs -f stt-tts-gateway

# View with debug logging
STT_MODEL_SIZE=base python start.py --log-level debug
```

## Development

### Project Structure

```
11-stt-tts-gateway/
├── src/
│   └── app.py              # Main FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Docker composition
├── test_api.py           # API test suite
├── start.py              # Python startup script
├── start.sh              # Shell startup script
└── README.md             # This file
```

### Adding New Features

1. **New TTS Voice**: Update `TTS_MODEL_NAME` environment variable
2. **Custom Audio Processing**: Modify `process_audio_*` functions in `app.py`
3. **Additional Endpoints**: Add routes to the FastAPI app

## License

This service is part of the OpenWebUI Suite. See project license for details.
