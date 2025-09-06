"""Simple async Redis-backed task queue with DLQ and depth limiting.
Not production-grade; provides basic enqueue, dequeue, ack/fail semantics.
"""
from __future__ import annotations
import os
import json
import asyncio
import time
from typing import Any, Dict, Optional

import redis.asyncio as redis  # type: ignore

QUEUE = os.getenv("TASK_QUEUE_NAME", "pipeline_tasks")
DLQ = os.getenv("TASK_DQL_NAME", "pipeline_tasks_dlq")
MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", "3"))
VIS_TIMEOUT = int(os.getenv("TASK_VISIBILITY_TIMEOUT", "120"))
MAX_DEPTH = int(os.getenv("TASK_MAX_DEPTH", "4"))


class TaskQueue:
    def __init__(self, url: str):
        self.url = url
        self._r: Optional[redis.Redis] = None

    async def connect(self):
        if self._r is None:
            self._r = redis.from_url(self.url, decode_responses=True)

    async def close(self):
        if self._r is not None:
            await self._r.close()
            self._r = None

    async def enqueue(self, payload: Dict[str, Any], depth: int = 0):
        if depth > MAX_DEPTH:
            if self._r:
                await self._r.lpush(
                    DLQ,
                    json.dumps({
                        "payload": payload,
                        "reason": "depth_exceeded"
                    })
                )
            return
        job = {
            "payload": payload,
            "retries": 0,
            "visible_at": time.time(),
            "depth": depth,
        }
        if self._r:
            await self._r.rpush(QUEUE, json.dumps(job))

    async def poll(self) -> Optional[Dict[str, Any]]:
        if not self._r:
            return None
        raw = await self._r.lpop(QUEUE)
        if not raw:
            return None
        job = json.loads(raw)
        if job["retries"] > MAX_RETRIES:
            await self._r.lpush(
                DLQ,
                json.dumps({
                    "payload": job["payload"],
                    "reason": "retries_exceeded"
                })
            )
            return None
        # visibility timer emulation: requeue with delay if needed
        job["visible_at"] = time.time() + VIS_TIMEOUT
        return job

    async def fail(self, job: Dict[str, Any]):
        job["retries"] += 1
        if self._r:
            await self._r.lpush(QUEUE, json.dumps(job))

    async def succeed(self, job: Dict[str, Any]):
        # nothing else to do (ack is implicit by removal)
        return


async def worker_loop(q: TaskQueue, handler):
    await q.connect()
    while True:
        job = await q.poll()
        if not job:
            await asyncio.sleep(1.0)
            continue
        try:
            await handler(job["payload"], job.get("depth", 0))
            await q.succeed(job)
        except Exception:  # pragma: no cover
            await q.fail(job)
