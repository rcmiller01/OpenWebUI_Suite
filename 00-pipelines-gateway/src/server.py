# 00-pipelines-gateway/src/server.py
from __future__ import annotations
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, AsyncIterator
import json
import os
import time
import asyncio
import uuid
import contextlib

from src.util.http import (  # type: ignore
    Svc,
    REQUEST_ID,
    init_http_client,
    close_http_client,
)
from src.tasks import TaskQueue, worker_loop  # type: ignore
from src.router.providers import get_model_router  # type: ignore

ENABLE_OTEL = os.getenv("ENABLE_OTEL", "false").lower() == "true"
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "pipelines-gateway")
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "0") or 0)
RATE_LIMIT_BURST = int(
    os.getenv("RATE_LIMIT_BURST", str(max(1, RATE_LIMIT_PER_MIN)))
)
REMOTE_CODE_ROUTING = (
    os.getenv("REMOTE_CODE_ROUTING", "true").lower() == "true"
)
REMOTE_CODE_MIN_CHARS = int(
    os.getenv("REMOTE_CODE_MIN_CHARS", "350") or 350
)
REMOTE_CODE_KEYWORDS = os.getenv(
    "REMOTE_CODE_KEYWORDS",
    (
        "optimize,refactor,algorithm,complexity,big o,asyncio,"  # noqa: E501
        "deadlock,thread,socket,performance,vectorize"
    ),
).lower().split(",")
PIPELINE_TIMEOUT = int(os.getenv("PIPELINE_TIMEOUT_SECONDS", "0") or 0)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TASK_WORKER_ENABLED = os.getenv(
    "TASK_WORKER_ENABLED", "false"
).lower() == "true"
TASK_QUEUE_NAME = os.getenv("TASK_QUEUE_NAME", "pipeline_tasks")
TASK_DQL_NAME = os.getenv("TASK_DQL_NAME", "pipeline_tasks_dlq")

if ENABLE_OTEL:
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import (  # type: ignore
            BatchSpanProcessor,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,  # type: ignore
        )
        from opentelemetry.instrumentation.fastapi import (  # type: ignore
            FastAPIInstrumentor,
        )

        resource = Resource.create({"service.name": OTEL_SERVICE_NAME})
        provider = TracerProvider(resource=resource)
        if OTEL_ENDPOINT:
            exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
            provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    except Exception:  # pragma: no cover - instrumentation optional
        ENABLE_OTEL = False

app = FastAPI(title="Pipelines Gateway", version="0.4.0")

if ENABLE_OTEL:
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception:  # pragma: no cover
        pass

# Shared HTTP client (future: reuse) placeholder for potential pooling
_shared_client = None  # reserved for future optimization
_task_queue: TaskQueue | None = None
_worker_task: asyncio.Task | None = None
_metrics: dict[str, int] = {
    "http_requests_total": 0,
    "chat_completions_total": 0,
    "chat_stream_total": 0,
    "rate_limited_total": 0,
    "timeouts_total": 0,
    "tool_calls_total": 0,
    "task_enqueued_total": 0,
}


# --- Rate Limiting Middleware (simple global or per-user bucket) ---
_TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local rate = tonumber(ARGV[2]) -- tokens per minute
local burst = tonumber(ARGV[3])
local ttl = 120
local bucket = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(bucket[1]) or burst
local ts = tonumber(bucket[2]) or now_ms
local elapsed = math.max(0, now_ms - ts)
local refill = (rate/60000.0) * elapsed
tokens = math.min(burst, tokens + refill)
if tokens < 1 then
    redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)
    redis.call('PEXPIRE', key, ttl*1000)
    return 0
else
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)
    redis.call('PEXPIRE', key, ttl*1000)
    return tokens
end
"""

 
async def _rate_limiter(request: Request) -> bool:
    if RATE_LIMIT_PER_MIN <= 0:
        return True
    try:
        import redis.asyncio as redis  # type: ignore
        r = redis.from_url(REDIS_URL, decode_responses=True)
        user_id = request.headers.get("X-User-Id") or "global"
        key = f"tb:{user_id}"
        now_ms = int(time.time() * 1000)
        remain = await r.eval(
            _TOKEN_BUCKET_SCRIPT,
            1,
            key,
            now_ms,
            RATE_LIMIT_PER_MIN,
            RATE_LIMIT_BURST,
        )
        return remain != 0
    except Exception:
        return True


@app.middleware("http")
async def rate_limit_and_timeout(request: Request, call_next):
    _metrics["http_requests_total"] += 1  # best-effort in-memory counter
    # rate limit
    allowed = await _rate_limiter(request)
    if not allowed:
        _metrics["rate_limited_total"] += 1
        return Response(status_code=429, content="Rate limit exceeded")
    # timeout wrapper
    if PIPELINE_TIMEOUT and request.url.path.startswith("/v1/chat/"):
        try:
            return await asyncio.wait_for(
                call_next(request), timeout=PIPELINE_TIMEOUT
            )
        except asyncio.TimeoutError:
            _metrics["timeouts_total"] += 1
            return Response(status_code=504, content="Gateway timeout")
    return await call_next(request)


# Middleware: correlation / request id
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    token = REQUEST_ID.set(rid)
    try:
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response
    finally:
        REQUEST_ID.reset(token)


@app.on_event("startup")
async def _load_services():
    await init_http_client()
    with open(os.getenv("SERVICES_PATH", "config/services.json"), "r") as f:
        app.state.services = {k: Svc(v) for k, v in json.load(f).items()}
    # Task queue setup
    global _task_queue, _worker_task
    _task_queue = TaskQueue(REDIS_URL)
    if TASK_WORKER_ENABLED:
        async def _handler(payload, depth):
            # Minimal async processing: run full pipeline and discard result
            try:
                ctx = {
                    "messages": payload["messages"],
                    "user_id": payload.get("user", "anon"),
                }
                ctx = await _pre(ctx)
                ctx = await _mid(ctx)
                await _post(ctx)
            except Exception:
                pass
        _worker_task = asyncio.create_task(worker_loop(_task_queue, _handler))


@app.on_event("shutdown")
async def _shutdown():
    await close_http_client()
    global _worker_task
    if _worker_task:
        _worker_task.cancel()
        with contextlib.suppress(Exception):  # type: ignore
            await _worker_task


def _sys_prompt_base() -> str:
    return ("You are a single, consistent assistant. Be helpful, "
            "concise, and truthful.")


async def _pre(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich ctx with intent, memory, affect, drive; build system addendum.
    Fault tolerant & partly parallel."""
    S = app.state.services
    user_msg = ctx["messages"][-1]
    user_text = user_msg["content"]

    # Intent first (drives lanes)
    try:
        intent = await S["intent_router"].post(
            "/classify", {"text": user_text}
        )
    except Exception as e:
        await S["telemetry"].post(
            "/log", {"event": "intent_error", "payload": {"error": str(e)}}
        )
        intent = {"intent": "general"}
    ctx["intent"] = intent
    lane = intent.get("intent")

    # --- Heuristic: decide if remote (larger) model needed ---
    if REMOTE_CODE_ROUTING:
        text_lc = user_text.lower()
        code_fence = (
            "```" in user_text or any(
                sym in user_text for sym in [
                    "def ", "class ", "import ", "#include",
                    "public static", "async def"
                ]
            )
        )
        keyword_hit = any(
            k.strip() and k.strip() in text_lc for k in REMOTE_CODE_KEYWORDS
        )
        long_input = len(user_text) >= REMOTE_CODE_MIN_CHARS
        upscale_signal = any(
            kw in text_lc for kw in [
                "gpt-4", "larger model", "highest quality", "best model"
            ]
        )
        if code_fence or keyword_hit or long_input or upscale_signal:
            # mark remote need; downstream router uses this flag
            intent["needs_remote"] = True  # type: ignore

    def _inject_obs(obs_text: str):
        if not obs_text:
            return
        ctx.setdefault("system_addenda", []).append(
            f"[VISION_OBS]\n{obs_text[:1500]}"
        )

    # --- IMAGE path ---
    if lane == "mm_image":
        image_url = user_msg.get("image_url")
        image_b64 = user_msg.get("image_b64")
        payload = {"image_url": image_url, "image_b64": image_b64,
                   "prompt": "Describe salient content, any text, "
                             "charts, and safety/PII notes."}

        # Prefer local FastVLM, else remote multimodal
        obs = None
        try:
            obs = await S["fastvlm"].post("/analyze", payload)
        except Exception as e:
            # Log fallback to telemetry
            await S["telemetry"].post("/log",
                                      {"event": "multimodal_fallback",
                                       "payload": {"from": "fastvlm",
                                                   "to": "multimodal",
                                                   "intent": lane,
                                                   "error": str(e)}})
            try:
                obs = await S["multimodal"].post("/mm/image", payload)
            except Exception as e2:
                # Log complete failure
                await S["telemetry"].post("/log",
                                          {"event": "multimodal_failure",
                                           "payload": {"intent": lane,
                                                       "error": str(e2)}})
                obs = None

        if obs and obs.get("observations"):
            # Join all observations into a compact paragraph/bullets
            joined = "\n".join(f"- {o.get('text', '')}"
                               for o in obs["observations"] if o.get("text"))
            _inject_obs(joined)

    # --- AUDIO path ---
    if lane == "mm_audio":
        # For simplicity, assume multimodal router handles file upload
        # and we just request analysis via reference
        obs = None
        try:
            # If you have an audio reference in the message:
            audio_ref = user_msg.get("audio_ref")
            if audio_ref:
                obs = await S["multimodal"].post("/mm/audio_json",
                                                 {"audio_url": audio_ref})
        except Exception as e:
            # Log audio_json fallback failure to telemetry
            await S["telemetry"].post("/log",
                                      {"event": "multimodal_fallback",
                                       "payload": {"from": "audio_json",
                                                   "to": "none",
                                                   "intent": lane,
                                                   "error": str(e)}})
            obs = None

        # If we got transcript/summary, inject it
        if obs and (obs.get("transcript") or obs.get("observations")):
            bullets = []
            if obs.get("transcript"):
                bullets.append(f"TRANSCRIPT (short): "
                               f"{obs['transcript'][:400]}")
            for o in (obs.get("observations") or [])[:3]:
                if o.get("text"):
                    bullets.append(f"- {o['text']}")
            _inject_obs("\n".join(bullets))

    # Parallel enrichment (memory summary / retrieval, affect + tone, drive)
    user_id = ctx.get("user_id", "anon")

    async def _mem_retrieve():
        try:
            return await S["memory"].get(
                "/mem/retrieve", user_id=user_id,
                intent=intent.get("intent"), k=4
            )
        except Exception as e:
            await S["telemetry"].post(
                "/log",
                {
                    "event": "memory_retrieve_error",
                    "payload": {"error": str(e)}
                }
            )
            return {"items": []}

    async def _mem_summary():
        try:
            return await S["memory"].get("/mem/summary", user_id=user_id)
        except Exception as e:
            await S["telemetry"].post(
                "/log",
                {
                    "event": "memory_summary_error",
                    "payload": {"error": str(e)}
                }
            )
            return {"summary": ""}

    async def _affect():
        try:
            a = await S["feeling"].post(
                "/affect/analyze", {"text": user_text}
            )
            t = await S["feeling"].post(
                "/affect/tone", {"affect": a}
            )
            return a, t
        except Exception as e:
            await S["telemetry"].post(
                "/log",
                {"event": "affect_error", "payload": {"error": str(e)}}
            )
            return {}, {"tone_policy": []}

    async def _drive():
        try:
            d = await S["drive"].get(
                "/drive/get", user_id=user_id
            )
            p = await S["drive"].post(
                "/drive/policy", {"state": d}
            )
            return d, p
        except Exception as e:
            await S["telemetry"].post(
                "/log",
                {"event": "drive_error", "payload": {"error": str(e)}}
            )
            return {}, {"hints": {}}

    mem, summary, affect_tone, drive_policy = await asyncio.gather(
        _mem_retrieve(), _mem_summary(), _affect(), _drive()
    )
    affect, tone = affect_tone
    drive, policy = drive_policy

    # Optional policy lane application to build lane-specific system prompt
    # (non-blocking; falls back silently on error)
    lane_policy_prompt = None
    try:
        lane_name = lane or "general"
        if lane_name and lane_name not in ("general", "mm_image", "mm_audio"):
            apply_payload = {
                "lane": lane_name,
                "system": _sys_prompt_base(),
                "user": user_text,
                "affect": affect or {
                    "emotion": "neutral", "intensity": 0.0
                },
                "drive": {
                    "energy": drive.get("energy", 0),
                    "focus": drive.get("focus", 0)
                }
            }
            pol_apply = await S["policy"].post("/policy/apply", apply_payload)
            lane_policy_prompt = pol_apply.get("system_final")
            ctx["policy_validators"] = pol_apply.get("validators", [])
    except Exception as e:
        await S["telemetry"].post(
            "/log",
            {
                "event": "policy_apply_error",
                "payload": {"error": str(e), "lane": lane}
            }
        )

    # Assemble system prompt
    addendum = []
    addendum.append(f"[MEMORY SUMMARY]\n{summary.get('summary', '')}")
    if mem.get("items"):
        joined = "\n".join(f"- {m['text']}" for m in mem["items"])
        addendum.append(f"[RELEVANT EPISODES]\n{joined}")
    addendum.append(f"[AFFECT]\n{json.dumps(affect)}")
    addendum.append(f"[TONE_POLICY]\n{','.join(tone.get('tone_policy', []))}")
    addendum.append(f"[DRIVE_HINTS]\n{json.dumps(policy.get('hints', {}))}")
    # Insert lane policy system prompt (if any) first for precedence
    if lane_policy_prompt:
        ctx.setdefault("system_addenda", []).insert(0, lane_policy_prompt)
    ctx.setdefault("system_addenda", []).append("\n\n".join(addendum))

    # Store for mid/post
    ctx["__affect"] = affect
    ctx["__tone"] = tone
    ctx["__drive"] = drive
    return ctx


async def _execute_tool(
    S, call: Dict[str, Any], messages: List[Dict[str, Any]]
):
    tool_name = call["function"]["name"]
    try:
        tool_args = json.loads(call["function"].get("arguments", "{}"))
    except Exception:
        tool_args = {}
    tool_res = await S["tools"].post(
        "/tools/exec", {"name": tool_name, "arguments": tool_args}
    )
    messages.append({
        "role": "tool", "name": tool_name,
        "content": json.dumps(tool_res)
    })
    return messages

 
async def _tool_call_loop(
    router, S, base_messages: List[Dict[str, Any]],
    tool_list: List[Dict[str, Any]], max_iters: int = 3
):
    messages = list(base_messages)
    for _ in range(max_iters):
        draft = await router.chat_complete({
            "messages": messages,
            "temperature": 0.3,
            "tools": tool_list
        })
        msg = draft["choices"][0]["message"]
        tcs = msg.get("tool_calls")
        if not tcs:
            return draft, messages
        # execute sequentially (could parallelize later)
        for call in tcs:
            messages = await _execute_tool(S, call, messages)
            _metrics["tool_calls_total"] += 1
        # append assistant stub so conversation context grows
        if msg.get("content"):
            messages.append({"role": "assistant", "content": msg["content"]})
    return draft, messages


async def _mid(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Generation (with hidden helper & merger)"""
    S = app.state.services
    # Prepare messages: insert system base + addenda
    sys = [{"role": "system", "content": _sys_prompt_base()}]
    for add in ctx.get("system_addenda", []):
        sys.append({"role": "system", "content": add})
    messages = sys + ctx["messages"]

    # Tool exposure
    tools_schema = await S["tools"].get("/tools")
    tool_list = tools_schema.get("tools", [])

    # Decide router
    needs_remote = bool(ctx.get("intent", {}).get("needs_remote"))
    router = await get_model_router(needs_remote=needs_remote, model_hint=None)

    # Draft with iterative tool loop
    draft, messages_after = await _tool_call_loop(
        router, S, messages, tool_list
    )
    draft_text = draft["choices"][0]["message"].get("content", "")

    # 2) Optional hidden helper critique + merge
    merge_in = {
        "prompt": draft_text,
        "persona": "single-voice, consistent, concise",
        "tone_policy": ctx.get("__tone", {}).get("tone_policy", []),
        "budgets": {"time_ms": 1200, "tokens": 120}
    }
    merged = await S["merger"].post("/compose", merge_in)
    ctx["final_text"] = merged.get("text") or merged.get("final_text",
                                                         draft_text)
    return ctx


async def _post(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Memory write & telemetry"""
    S = app.state.services
    # Extract memory candidates (very simple v1: last assistant + user msg)
    user_id = ctx.get("user_id", "anon")
    last_user = ctx["messages"][-1]["content"]
    assistant = ctx.get("final_text", "")
    await S["memory"].post("/mem/candidates",
                           {"user_id": user_id, "text": last_user,
                            "tags": ["user"], "confidence": 0.7})
    await S["memory"].post("/mem/candidates",
                           {"user_id": user_id, "text": assistant,
                            "tags": ["assistant"], "confidence": 0.6})
    # Policy validation and repair
    try:
        pol = await S["policy"].post("/policy/validate", {
            "lane": ctx.get("intent", {}).get("intent", "general"),
            "text": ctx.get("final_text", "")
        })
        if not pol.get("ok", True):
            ctx["final_text"] = pol.get("repaired", ctx["final_text"])
    except Exception as e:
        # Log policy validation failure but don't block the response
        await S["telemetry"].post("/log",
                                  {"event": "policy_validation_error",
                                   "payload": {"error": str(e),
                                               "intent": ctx.get("intent",
                                                                 {})}})
    # Telemetry
    await S["telemetry"].post("/log", {
        "event": "chat_turn",
        "payload": {
            "intent": ctx.get("intent"),
            "len_out": len(ctx.get("final_text", ""))
        }
    })
    return ctx


# ---------- OpenAI-compatible endpoint ----------
@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    if not body.get("messages"):
        return {"error": "messages required"}
    ctx = {"messages": body["messages"], "user_id": body.get("user", "anon")}
    ctx = await _pre(ctx)
    ctx = await _mid(ctx)
    ctx = await _post(ctx)
    _metrics["chat_completions_total"] += 1
    return {
        "id": "owui-pipe-" + str(int(time.time() * 1000)),
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": ctx["final_text"]}
        }],
        "model": (
            os.getenv("OPENROUTER_MODEL")
            if ctx.get("intent", {}).get("needs_remote")
            else os.getenv("DEFAULT_LOCAL_MODEL")
        )
    }


@app.post("/v1/chat/completions/stream")
async def chat_completions_stream(req: Request):
    body = await req.json()
    if not body.get("messages"):
        return {"error": "messages required"}
    ctx = {"messages": body["messages"], "user_id": body.get("user", "anon")}
    ctx = await _pre(ctx)
    S = app.state.services
    sys_msgs = [{"role": "system", "content": _sys_prompt_base()}]
    for add in ctx.get("system_addenda", []):
        sys_msgs.append({"role": "system", "content": add})
    all_msgs = sys_msgs + ctx["messages"]
    tools_schema = await S["tools"].get("/tools")
    tool_list = tools_schema.get("tools", [])
    needs_remote = bool(ctx.get("intent", {}).get("needs_remote"))
    router = await get_model_router(needs_remote=needs_remote, model_hint=None)

    async def _gen() -> AsyncIterator[bytes]:
        async for delta in router.chat_stream({
            "messages": all_msgs,
            "tools": tool_list
        }):
            yield json.dumps({"delta": delta}).encode() + b"\n"
        yield b"[DONE]"

    _metrics["chat_stream_total"] += 1
    return StreamingResponse(_gen(), media_type="application/json")


@app.post("/tasks/enqueue")
async def enqueue_task(req: Request):
    body = await req.json()
    if not _task_queue:
        return {"error": "task queue disabled"}
    await _task_queue.connect()
    await _task_queue.enqueue({"messages": body.get("messages", [])}, depth=0)
    _metrics["task_enqueued_total"] += 1
    return {"enqueued": True}


@app.get("/tasks/dlq")
async def list_dlq(limit: int = 25):
    if not _task_queue:
        return {"error": "task queue disabled"}
    import redis.asyncio as redis  # type: ignore
    r = redis.from_url(REDIS_URL, decode_responses=True)
    # LRANGE returns newest to oldest depending on push order; adjust if needed
    items = await r.lrange(TASK_DQL_NAME, 0, limit - 1)
    return {"dlq": [json.loads(i) for i in items]}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "pipelines-gateway",
        "version": "0.4.0",
        "otel": ENABLE_OTEL,
        "rate_limit": RATE_LIMIT_PER_MIN,
        "rate_burst": RATE_LIMIT_BURST,
        "timeout": PIPELINE_TIMEOUT,
        "task_worker": TASK_WORKER_ENABLED,
        "metrics": _metrics,
    }


@app.get("/v1/models")
async def list_models():
    # Minimal static list; real impl could aggregate additional info
    model_id = os.getenv("DEFAULT_LOCAL_MODEL", "local-model")
    return {
        "object": "list",
        "data": [{"id": model_id, "object": "model"}],
    }


@app.get("/v1/tools")
async def list_tools():
    try:
        tools_schema = await app.state.services["tools"].get(  # type: ignore
            "/tools"
        )
        data = tools_schema.get("tools", [])
    except Exception:
        data = []
    return {"object": "list", "data": data}


@app.get("/metrics")
async def metrics():  # simple in-memory counters (reset on restart)
    lines: list[str] = []
    for k, v in _metrics.items():
        lines.append(f"# TYPE {k} counter")
        lines.append(f"{k} {v}")
    body = "\n".join(lines) + "\n"
    return Response(body, media_type="text/plain; version=0.0.4")
