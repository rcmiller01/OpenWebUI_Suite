"""
STT-TTS Gateway Service
Provides local speech-to-text and text-to-speech capabilities
"""

import base64
import logging
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn
from faster_whisper import WhisperModel
from TTS.api import TTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
STT_MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "base")
TTS_MODEL_NAME = os.getenv(
    "TTS_MODEL_NAME", "tts_models/en/ljspeech/tacotron2-DDC_ph"
)
AUDIO_STORAGE_PATH = Path(os.getenv("AUDIO_STORAGE_PATH", "./audio"))
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
).split(",")

# Ensure audio storage directory exists
AUDIO_STORAGE_PATH.mkdir(exist_ok=True)

# Initialize models
stt_model = None
tts_model = None


class STTRequest(BaseModel):
    """STT request model"""
    audio: str = Field(..., description="Base64 encoded audio data")
    format: str = Field(
        default="wav", description="Audio format (wav, mp3, flac)"
    )
    language: str = Field(
        default="auto", description="Language code or 'auto'"
    )
    timestamps: bool = Field(
        default=True, description="Include timestamps in response"
    )


class STTResponse(BaseModel):
    """STT response model"""
    text: str
    segments: List[Dict[str, Any]] = []
    language: str
    processing_time: float


class TTSRequest(BaseModel):
    """TTS request model"""
    text: str = Field(..., description="Text to synthesize")
    voice: str = Field(default="default", description="Voice to use")
    speed: float = Field(
        default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier"
    )
    timestamps: bool = Field(
        default=True, description="Include word timestamps"
    )


class TTSResponse(BaseModel):
    """TTS response model"""
    audio_url: str
    timestamps: List[Dict[str, Any]] = []
    duration: float
    processing_time: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    stt_model_loaded: bool
    tts_model_loaded: bool
    audio_storage_available: bool

app = FastAPI(
    title="STT-TTS Gateway",
    description="Local speech-to-text and text-to-speech service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STT cleanup configuration
AUD_DIR = os.getenv("AUDIO_STORAGE_PATH", "/tmp/owui_audio")
TTL_SEC = int(os.getenv("STT_TTL_SECONDS", "900"))       # 15 min
MAX_MB = int(os.getenv("STT_MAX_UPLOAD_MB", "25"))
os.makedirs(AUD_DIR, exist_ok=True)

def _cleanup_loop():
    while True:
        now = time.time()
        try:
            for f in os.listdir(AUD_DIR):
                p = os.path.join(AUD_DIR, f)
                if os.path.isfile(p) and (now - os.path.getmtime(p) > TTL_SEC):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(120)


@app.on_event("startup")
def _start_cleanup():
    threading.Thread(target=_cleanup_loop, daemon=True).start()

def initialize_models():
    """Initialize STT and TTS models"""
    global stt_model, tts_model

    try:
        logger.info(f"Loading STT model: {STT_MODEL_SIZE}")
        stt_model = WhisperModel(STT_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("STT model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load STT model: {e}")
        stt_model = None

    try:
        logger.info(f"Loading TTS model: {TTS_MODEL_NAME}")
        tts_model = TTS(TTS_MODEL_NAME).to("cpu")
        logger.info("TTS model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load TTS model: {e}")
        tts_model = None

def decode_audio_base64(audio_b64: str, format: str) -> bytes:
    """Decode base64 audio data"""
    try:
        audio_data = base64.b64decode(audio_b64)
        return audio_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {e}")

def save_temp_audio(audio_data: bytes, format: str) -> str:
    """Save audio data to temporary file"""
    with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
        temp_file.write(audio_data)
        return temp_file.name

def validate_audio_size(audio_data: bytes) -> None:
    """Validate audio file size"""
    size_mb = len(audio_data) / (1024 * 1024)
    if size_mb > MAX_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large: {size_mb:.1f}MB (max: {MAX_MB}MB)"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    initialize_models()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if stt_model and tts_model else "degraded",
        stt_model_loaded=stt_model is not None,
        tts_model_loaded=tts_model is not None,
        audio_storage_available=AUDIO_STORAGE_PATH.exists()
    )

@app.post("/stt", response_model=STTResponse)
async def speech_to_text(request: STTRequest):
    """Convert speech to text"""
    if not stt_model:
        raise HTTPException(status_code=503, detail="STT model not loaded")

    start_time = time.time()

    try:
        # Decode audio
        audio_data = decode_audio_base64(request.audio, request.format)
        validate_audio_size(audio_data)

        # Save to temporary file
        temp_file = save_temp_audio(audio_data, request.format)

        try:
            # Transcribe audio
            segments, info = stt_model.transcribe(
                temp_file,
                language=request.language if request.language != "auto" else None,
                beam_size=5,
                patience=1,
                length_penalty=1,
                repetition_penalty=1,
                no_repeat_ngram_size=0,
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,
                prompt_reset_on_temperature=0.5,
                initial_prompt=None,
                prefix=None,
                suppress_blank=True,
                suppress_tokens=[-1],
                without_timestamps=False,
                max_initial_timestamp=1.0,
                hallucination_silence_threshold=None,
            )

            # Process segments
            text = ""
            segment_list = []

            for segment in segments:
                text += segment.text
                if request.timestamps:
                    segment_list.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip()
                    })

            processing_time = time.time() - start_time

            return STTResponse(
                text=text.strip(),
                segments=segment_list,
                language=info.language,
                processing_time=round(processing_time, 3)
            )

        finally:
            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"STT processing error: {e}")
        raise HTTPException(status_code=500, detail=f"STT processing failed: {str(e)}")

@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest, background_tasks: BackgroundTasks):
    """Convert text to speech"""
    if not tts_model:
        raise HTTPException(status_code=503, detail="TTS model not loaded")

    start_time = time.time()

    try:
        # Generate unique filename
        audio_filename = f"generated_{uuid.uuid4().hex}.wav"
        audio_path = AUDIO_STORAGE_PATH / audio_filename

        # Synthesize speech
        tts_model.tts_to_file(
            text=request.text,
            file_path=str(audio_path),
            speed=request.speed
        )

        # Calculate duration (simplified)
        duration = len(request.text.split()) * 0.3  # Rough estimate

        # Generate timestamps if requested
        timestamps = []
        if request.timestamps:
            words = request.text.split()
            current_time = 0.0
            for word in words:
                word_duration = len(word) * 0.1  # Rough estimate per character
                timestamps.append({
                    "word": word,
                    "start": round(current_time, 2),
                    "end": round(current_time + word_duration, 2)
                })
                current_time += word_duration

        processing_time = time.time() - start_time

        # Schedule cleanup
        background_tasks.add_task(cleanup_old_audio)

        return TTSResponse(
            audio_url=f"/audio/{audio_filename}",
            timestamps=timestamps,
            duration=round(duration, 2),
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"TTS processing error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS processing failed: {str(e)}")

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Retrieve generated audio file"""
    audio_path = AUDIO_STORAGE_PATH / filename

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/wav",
        filename=filename
    )

async def cleanup_old_audio():
    """Clean up old audio files (older than 1 hour)"""
    try:
        cutoff_time = time.time() - 3600  # 1 hour ago

        for audio_file in AUDIO_STORAGE_PATH.glob("generated_*.wav"):
            if audio_file.stat().st_mtime < cutoff_time:
                audio_file.unlink(missing_ok=True)
                logger.info(f"Cleaned up old audio file: {audio_file.name}")

    except Exception as e:
        logger.error(f"Audio cleanup error: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8089,
        reload=True,
        log_level="info"
    )
