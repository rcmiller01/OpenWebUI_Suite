from __future__ import annotations
import os
import io
import base64
import httpx
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import torch
from transformers import AutoProcessor


# Lazy import to avoid heavy init at import time
model = None
processor = None


def get_model():
    global model, processor
    if model is not None:
        return model, processor
    model_id = os.getenv("FASTVLM_MODEL", "apple/fastvlm-2.7b")
    device = os.getenv("DEVICE", "cuda")
    dtype = getattr(torch, os.getenv("TORCH_DTYPE", "float16"))
    from transformers import AutoModelForCausalLM
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None
    )
    if device == "cuda":
        model.to("cuda")
    return model, processor


def load_image(image_url: Optional[str],
               image_b64: Optional[str]) -> Image.Image:
    if image_url:
        resp = httpx.get(image_url, timeout=20)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    if image_b64:
        data = base64.b64decode(image_b64)
        return Image.open(io.BytesIO(data)).convert("RGB")
    raise HTTPException(400, "Provide image_url or image_b64")


app = FastAPI(title="FastVLM Sidecar", version="0.1.0")


class Req(BaseModel):
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    prompt: Optional[str] = None
    max_new_tokens: Optional[int] = None


DEFAULT_PROMPT = (
    "Describe the image succinctly in 3–6 bullet points. "
    "Call out visible text, diagrams/charts, and any safety or PII concerns. "
    "Be factual and avoid speculation."
)


@app.post("/analyze")
def analyze(req: Req):
    m, p = get_model()
    img = load_image(req.image_url, req.image_b64)
    prompt = (req.prompt or DEFAULT_PROMPT)[:1000]
    inputs = p(text=prompt, images=img, return_tensors="pt")
    device = "cuda" if next(m.parameters()).is_cuda else "cpu"
    inputs = {k: v.to(device) for k, v in inputs.items()}
    tokens = int(req.max_new_tokens or int(os.getenv("MAX_TOKENS", "192")))
    out = m.generate(**inputs, max_new_tokens=tokens)
    text = p.batch_decode(out, skip_special_tokens=True)[0].strip()
    return {"observations": [{"label": "scene", "text": text}], "safety": []}


@app.get("/healthz")
def healthz():
    return {"ok": True}
