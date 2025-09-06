ARG BASE_IMAGE=owui/base:py311
FROM ${BASE_IMAGE} as builder
WORKDIR /app
COPY requirements.txt ./requirements.txt
# Separate heavy ML deps to optimize caching
RUN grep -E '^(torch|torchaudio|faster-whisper|TTS)' requirements.txt > ml.txt || true \
 && grep -Ev '^(torch|torchaudio|faster-whisper|TTS)' requirements.txt > base.txt || true \
 && pip install -r base.txt -c /app/constraints.txt \
 && if [ -s ml.txt ]; then pip install -r ml.txt; fi
COPY src ./src

FROM ${BASE_IMAGE} as runtime
WORKDIR /app
ENV AUDIO_STORAGE_PATH=/app/audio
ARG PREFETCH_MODELS="false"
COPY --from=builder /app /app
RUN mkdir -p $AUDIO_STORAGE_PATH \
 && if [ "$PREFETCH_MODELS" = "true" ]; then \
     python - <<'PY'
from faster_whisper import WhisperModel
from TTS.api import TTS
import os
stt=os.getenv('STT_MODEL_SIZE','base');
tts=os.getenv('TTS_MODEL_NAME','tts_models/en/ljspeech/tacotron2-DDC_ph')
try:
    WhisperModel(stt, device='cpu', compute_type='int8')
except Exception as e:
    print('Prefetch STT failed', e)
try:
    TTS(tts)
except Exception as e:
    print('Prefetch TTS failed', e)
PY
    ; fi
EXPOSE 8089
HEALTHCHECK --interval=45s --timeout=10s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request,sys;\nurl='http://localhost:8089/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=5).read();\nexcept Exception:\n sys.exit(1)" || exit 1
CMD ["uvicorn","src.app:app","--host","0.0.0.0","--port","8089"]
