from __future__ import annotations
import os
import base64
import httpx
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from urllib.parse import urlparse
from .security import verify_sig

MAX_BYTES = int(os.getenv("MM_MAX_DOWNLOAD_BYTES", "10485760"))  # 10 MB

app = FastAPI(title="Multimodal Router", version="0.1.0")

# ---- Config / Prompts ----
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VISION_MODEL = os.getenv("VISION_MODEL", "openai/gpt-4o-mini")
AUDIO_MODEL = os.getenv("AUDIO_MODEL", "openai/gpt-4o-mini")
# optional direct-audio model

# Default, overridable prompts
PROMPT_IMAGE = os.getenv("PROMPT_IMAGE",
                         "You are a careful visual analyst. Describe the image "
                         "concisely in bullet points. Highlight text, "
                         "diagrams, charts, and safety/PII concerns. "
                         "Return only the facts you can see."
                         )

PROMPT_AUDIO = os.getenv("PROMPT_AUDIO",
                         "Transcribe the audio faithfully. Then summarize "
                         "key points and action items in 3 bullets."
                         )

# Local STT (fallback) — your 11-stt-tts-gateway
STT_URL = os.getenv("STT_URL", "http://stt-tts:8111/stt")


# ---- Schemas ----
class ImageIn(BaseModel):
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    prompt:    Optional[str] = None


class AudioJsonIn(BaseModel):
    audio_url: Optional[str] = None
    audio_b64: Optional[str] = None
    prompt: Optional[str] = None
    prefer_remote: bool = False


def _or_headers() -> Dict[str, str]:
    if not OPENROUTER_API_KEY:
        raise HTTPException(500, "OPENROUTER_API_KEY missing")
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer":  "http://localhost",
        "X-Title":       "OWUI-Pipelines-MMR"
    }


def _is_safe_url(u: str) -> bool:
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https")
    except Exception:
        return False


async def _safe_get_bytes(url: str) -> bytes:
    if not _is_safe_url(url):
        raise HTTPException(400, "Invalid URL scheme")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(url, follow_redirects=True)
        r.raise_for_status()
        if int(r.headers.get("content-length", "0")) > MAX_BYTES:
            raise HTTPException(413, "Payload too large")
        return r.content[:MAX_BYTES]


def _make_image_content(req: ImageIn) -> Any:
    if req.image_url:
        return {"type": "image_url", "image_url": {"url": req.image_url}}
    if req.image_b64:
        # must be data URL or raw b64; OpenRouter accepts base64
        # via "image" field for some models
        return {"type": "input_image", "image": req.image_b64}
    raise HTTPException(400, "Provide image_url or image_b64")


# ---- Endpoints ----

@app.post("/mm/image")
async def analyze_image(req: ImageIn, request: Request):
    raw = await request.body()
    await verify_sig(request, raw)
    """
    Analyze an image via a VLM on OpenRouter.
    Normalized output: { observations: [{label,text}], safety: [] }
    """
    if req.image_url and not _is_safe_url(req.image_url):
        raise HTTPException(400, "Invalid URL scheme")
    content_block = _make_image_content(req)
    prompt = (req.prompt or PROMPT_IMAGE)[:1000]

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                content_block
            ]}
        ],
        "temperature": 0.2
    }

    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(OPENROUTER_URL, json=payload, headers=_or_headers())
        r.raise_for_status()
        out = r.json()

    text = out["choices"][0]["message"].get("content", "").strip()
    # Very small, consistent schema:
    return {
        "observations": [{"label": "scene", "text": text}],
        "safety": []
    }


@app.post("/mm/audio")
async def analyze_audio(
    file: UploadFile = File(...),
    prompt: str = Form(default=PROMPT_AUDIO),
    prefer_remote: bool = Form(default=False)
):
    """
    Analyze audio: default path uses local STT, then summarizes.
    If prefer_remote=True and AUDIO_MODEL supports direct audio,
    route to OpenRouter. Normalized output: { transcript: "...",
    observations: [] }
    """
    data = await file.read()
    if not data or len(data) == 0:
        raise HTTPException(400, "Empty audio")

    if prefer_remote:
        # Try direct audio VLM (may vary by model/provider)
        # Many OpenRouter models expect URL or specific audio block formats.
        # We'll fall back to local STT if remote fails.
        try:
            b64 = base64.b64encode(data).decode()
            payload = {
                "model": AUDIO_MODEL,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt[:1000]},
                        {"type": "input_audio", "audio": {
                            "data": b64,
                            "mime_type": file.content_type or "audio/wav"
                        }}
                    ]}
                ],
                "temperature": 0.0
            }
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(OPENROUTER_URL, json=payload,
                                 headers=_or_headers())
                r.raise_for_status()
                out = r.json()
            content = out["choices"][0]["message"].get("content", "").strip()
            # Heuristic split: first line transcript, rest summary
            # (if model returned text only)
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            transcript = lines[0] if lines else ""
            summary = "\n".join(lines[1:]) if len(lines) > 1 else ""
            return {"transcript": transcript,
                    "observations": [{"label": "summary", "text": summary}]}
        except Exception:
            # Fall back to local STT
            pass

    # Local STT path
    files = {"audio": (file.filename, data, file.content_type or "audio/wav")}
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(STT_URL, files=files)
        r.raise_for_status()
        stt = r.json()

    transcript = stt.get("text", "").strip()
    # Ask OpenRouter (text-only) to summarize
    payload = {
        "model": VISION_MODEL,  # text models work too
        "messages": [{"role": "user", "content":
                      f"{PROMPT_AUDIO}\n\nTRANSCRIPT:\n{transcript[:8000]}"}],
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r2 = await c.post(OPENROUTER_URL, json=payload, headers=_or_headers())
        r2.raise_for_status()
        out2 = r2.json()

    summary = out2["choices"][0]["message"].get("content", "").strip()
    return {
        "transcript": transcript,
        "observations": [{"label": "summary", "text": summary}]
    }


@app.post("/mm/audio_json")
async def analyze_audio_json(req: AudioJsonIn, request: Request):
    raw = await request.body()
    await verify_sig(request, raw)
    """
    Analyze audio from JSON input (URL or base64).
    Uses local STT, then summarizes with OpenRouter.
    Normalized output: { transcript: "...", observations: [] }
    """
    if req.audio_url:
        data = await _safe_get_bytes(req.audio_url)
    elif req.audio_b64:
        data = base64.b64decode(req.audio_b64)
    else:
        raise HTTPException(400, "Provide audio_url or audio_b64")

    # Local STT
    files = {"audio": ("input.wav", data, "audio/wav")}
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(STT_URL, files=files)
        r.raise_for_status()
        stt = r.json()

    transcript = stt.get("text", "").strip()

    # Summarize with OpenRouter (text)
    prompt = req.prompt or PROMPT_AUDIO
    payload = {
        "model": VISION_MODEL,
        "messages": [{"role": "user", "content":
                      f"{prompt}\n\nTRANSCRIPT:\n{transcript[:8000]}"}],
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r2 = await c.post(OPENROUTER_URL, json=payload, headers=_or_headers())
        r2.raise_for_status()
        out2 = r2.json()

    summary = out2["choices"][0]["message"].get("content", "").strip()

    return {
        "transcript": transcript,
        "observations": [{"label": "summary", "text": summary}]
    }


@app.get("/healthz")
def health():
    return {"ok": True}
