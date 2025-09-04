# 00-pipelines-gateway/src/util/http.py
from __future__ import annotations
import httpx
import os
import hmac
import hashlib
import json
from typing import Any, Dict


class Svc:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.secret = os.getenv("SUITE_SHARED_SECRET")  # optional

    async def get(self, path: str, **params):
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self.base}{path}", params=params)
            r.raise_for_status()
            return r.json()

    async def post(self, path: str, payload: Dict[str, Any]):
        headers = {}
        if self.secret is not None and payload is not None:
            raw = json.dumps(payload, separators=(",", ":")).encode()
            mac = hmac.new(self.secret.encode(), raw,
                           hashlib.sha256).hexdigest()
            headers["X-SUITE-SIG"] = mac
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{self.base}{path}", json=payload,
                             headers=headers)
            r.raise_for_status()
            return r.json()
