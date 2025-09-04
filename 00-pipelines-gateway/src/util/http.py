# 00-pipelines-gateway/src/util/http.py
from __future__ import annotations
import httpx
from typing import Any, Dict


class Svc:
    def __init__(self, base: str):
        self.base = base.rstrip("/")

    async def get(self, path: str, **params):
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self.base}{path}", params=params)
            r.raise_for_status()
            return r.json()

    async def post(self, path: str, payload: Dict[str, Any]):
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{self.base}{path}", json=payload)
            r.raise_for_status()
            return r.json()
