# 00-pipelines-gateway/src/router/providers.py
from __future__ import annotations
import os
import httpx
from typing import AsyncIterator, Dict, Any

OR_KEY = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OR_URL = "https://openrouter.ai/api/v1/chat/completions"

OLLAMA = os.getenv("OLLAMA_BASE", "http://localhost:11434")
LOCAL_MODEL = os.getenv("DEFAULT_LOCAL_MODEL", "qwen2.5:3b-instruct-q4_K_M")


class ModelRouter:
    def __init__(self, needs_remote: bool = False,
                 model_hint: str | None = None):
        self.needs_remote = needs_remote
        self.model_hint = model_hint

    async def chat_complete(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Non-stream convenience; returns OpenAI-shaped dict with
        choices[0].message.content"""
        if self.needs_remote:
            return await self._openrouter_complete(prompt)
        return await self._ollama_complete(prompt)

    async def chat_stream(self, prompt: Dict[str, Any]) -> AsyncIterator[str]:
        """Yields text deltas (already detokenized)."""
        if self.needs_remote:
            async for chunk in self._openrouter_stream(prompt):
                yield chunk
            return
        async for chunk in self._ollama_stream(prompt):
            yield chunk

    # -------- OpenRouter ----------
    async def _openrouter_complete(self, prompt: Dict[str, Any]) \
            -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {OR_KEY}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "OWUI-Pipelines"
        }
        data = {
            "model": self.model_hint or OR_MODEL,
            "messages": prompt["messages"],
            "temperature": prompt.get("temperature", 0.4),
            "tools": prompt.get("tools")
        }
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(OR_URL, json=data, headers=headers)
            r.raise_for_status()
            return r.json()

    async def _openrouter_stream(self, prompt: Dict[str, Any]) \
            -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {OR_KEY}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "OWUI-Pipelines"
        }
        data = {
            "model": self.model_hint or OR_MODEL,
            "messages": prompt["messages"],
            "stream": True
        }
        async with httpx.AsyncClient(timeout=None) as c:
            async with c.stream("POST", OR_URL,
                                json=data, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    if line.strip() == "data: [DONE]":
                        break
                    try:
                        delta = line.removeprefix("data: ").strip()
                        j = httpx.Response(200, text=delta).json()
                        yield j["choices"][0]["delta"].get("content", "")
                    except Exception:
                        continue

    # -------- Ollama ----------
    async def _ollama_complete(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        model = self.model_hint or LOCAL_MODEL
        data = {
            "model": model,
            "messages": prompt["messages"],
            "stream": False,
            "options": {"temperature": prompt.get("temperature", 0.4)}
        }
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{OLLAMA.rstrip('/')}/api/chat", json=data)
            r.raise_for_status()
            msg = r.json().get("message", {}).get("content", "")
            return {"choices": [{"message": {"content": msg}}]}

    async def _ollama_stream(self, prompt: Dict[str, Any]) \
            -> AsyncIterator[str]:
        model = self.model_hint or LOCAL_MODEL
        data = {
            "model": model,
            "messages": prompt["messages"],
            "stream": True,
            "options": {"temperature": prompt.get("temperature", 0.4)}
        }
        async with httpx.AsyncClient(timeout=None) as c:
            async with c.stream("POST", f"{OLLAMA.rstrip('/')}/api/chat",
                                json=data) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        j = httpx.Response(200, text=line).json()
                        content = j.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue


async def get_model_router(needs_remote: bool,
                           model_hint: str | None = None) -> ModelRouter:
    return ModelRouter(needs_remote=needs_remote, model_hint=model_hint)
