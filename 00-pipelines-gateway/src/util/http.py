# 00-pipelines-gateway/src/util/http.py
from __future__ import annotations
import httpx
import os
import hmac
import hashlib
import json
import contextvars
from typing import Any, Dict, Optional

# Per-request correlation id (set by gateway middleware)
REQUEST_ID: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


_CLIENT: httpx.AsyncClient | None = None


async def init_http_client():  # called on app startup
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(timeout=30)


async def close_http_client():  # called on app shutdown
    global _CLIENT
    if _CLIENT is not None:
        await _CLIENT.aclose()
        _CLIENT = None


class Svc:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.secret = os.getenv("SUITE_SHARED_SECRET")  # optional

    async def get(self, path: str, **params):
        headers = {}
        rid = REQUEST_ID.get()
        if rid:
            headers["X-Request-Id"] = rid
        client = _CLIENT or httpx.AsyncClient(timeout=30)
        r = await client.get(
            f"{self.base}{path}", params=params, headers=headers
        )
        r.raise_for_status()
        return r.json()

    async def post(self, path: str, payload: Dict[str, Any]):
        headers = {}
        rid = REQUEST_ID.get()
        if rid:
            headers["X-Request-Id"] = rid
        if self.secret is not None and payload is not None:
            raw = json.dumps(payload, separators=(",", ":")).encode()
            mac = hmac.new(
                self.secret.encode(), raw, hashlib.sha256
            ).hexdigest()
            headers["X-SUITE-SIG"] = mac
        client = _CLIENT or httpx.AsyncClient(timeout=60)
        r = await client.post(
            f"{self.base}{path}", json=payload, headers=headers
        )
        r.raise_for_status()
        return r.json()
