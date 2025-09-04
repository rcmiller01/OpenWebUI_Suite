# 00-pipelines-gateway/src/server.py
from __future__ import annotations
from fastapi import FastAPI, Request
from typing import Dict, Any, List
import json
import os
import time

from src.util.http import Svc
from src.router.providers import get_model_router

app = FastAPI(title="Pipelines Gateway", version="0.2.0")


@app.on_event("startup")
async def _load_services():
    with open(os.getenv("SERVICES_PATH", "config/services.json"), "r") as f:
        app.state.services = {k: Svc(v) for k, v in json.load(f).items()}


def _sys_prompt_base() -> str:
    return ("You are a single, consistent assistant. Be helpful, "
            "concise, and truthful.")


async def _pre(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich ctx with intent, memory, affect, drive; build system addendum"""
    S = app.state.services
    user_text = ctx["messages"][-1]["content"]
    # 1) intent
    intent = await S["intent_router"].post("/classify", {"text": user_text})
    ctx["intent"] = intent

    # Multimodal integration: inject vision/audio observations
    lane = intent.get("intent")
    user_msg = ctx["messages"][-1]

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

    # 2) memory
    mem = await S["memory"].get("/mem/retrieve",
                                user_id=ctx.get("user_id", "anon"),
                                intent=intent["intent"], k=4)
    summary = await S["memory"].get("/mem/summary",
                                    user_id=ctx.get("user_id", "anon"))
    # 3) affect
    affect = await S["feeling"].post("/affect/analyze", {"text": user_text})
    tone = await S["feeling"].post("/affect/tone", {"affect": affect})
    # 4) drive
    drive = await S["drive"].get("/drive/get",
                                 user_id=ctx.get("user_id", "anon"))
    policy = await S["drive"].post("/drive/policy", {"state": drive})

    # Assemble system prompt
    addendum = []
    addendum.append(f"[MEMORY SUMMARY]\n{summary.get('summary', '')}")
    if mem.get("items"):
        joined = "\n".join(f"- {m['text']}" for m in mem["items"])
        addendum.append(f"[RELEVANT EPISODES]\n{joined}")
    addendum.append(f"[AFFECT]\n{json.dumps(affect)}")
    addendum.append(f"[TONE_POLICY]\n{','.join(tone.get('tone_policy', []))}")
    addendum.append(f"[DRIVE_HINTS]\n{json.dumps(policy.get('hints', {}))}")
    ctx.setdefault("system_addenda", []).append("\n\n".join(addendum))

    # Store for mid/post
    ctx["__affect"] = affect
    ctx["__tone"] = tone
    ctx["__drive"] = drive
    return ctx


async def _tool_call_loop(messages: List[Dict[str, Any]]) \
        -> List[Dict[str, Any]]:
    """Simple tool-calling loop via Tool Hub"""
    S = app.state.services
    tools_schema = await S["tools"].get("/tools")
    # Attach tools to the next generation request; when tool_call returned
    # -> exec then append result
    return tools_schema  # we return schema; caller decides when to exec


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

    # 1) Primary draft (non-stream)
    draft_req = {"messages": messages, "temperature": 0.4,
                 "tools": tool_list}
    draft = await router.chat_complete(draft_req)
    draft_text = draft["choices"][0]["message"].get("content", "")

    # Optional: Handle tool calls (v1)
    tool_calls = draft["choices"][0]["message"].get("tool_calls")
    if tool_calls:
        # Execute exactly one tool (v1), append result to messages,
        # regenerate short answer
        call = tool_calls[0]
        tool_name = call["function"]["name"]
        tool_args = json.loads(call["function"].get("arguments", "{}"))
        tool_res = await S["tools"].post("/tools/exec",
                                         {"name": tool_name,
                                          "arguments": tool_args})
        messages += [{"role": "tool", "name": tool_name,
                     "content": json.dumps(tool_res)}]
        draft = await router.chat_complete({"messages": messages,
                                            "temperature": 0.3,
                                            "tools": tool_list})
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
    await S["telemetry"].post("/log",
                              {"event": "chat_turn",
                               "payload": {"intent": ctx.get("intent"),
                                           "len_out": len(assistant)}})
    return ctx


# ---------- OpenAI-compatible endpoint ----------
@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    ctx = {"messages": body["messages"], "user_id": body.get("user", "anon")}
    ctx = await _pre(ctx)
    ctx = await _mid(ctx)
    ctx = await _post(ctx)
    # Return OpenAI-shaped response
    return {
        "id": "owui-pipe-"+str(int(time.time()*1000)),
        "object": "chat.completion",
        "choices": [{"index": 0,
                     "message": {"role": "assistant",
                                 "content": ctx["final_text"]}}],
        "model": (os.getenv("OPENROUTER_MODEL") if
                  ctx.get("intent", {}).get("needs_remote") else
                  os.getenv("DEFAULT_LOCAL_MODEL"))
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "pipelines-gateway",
            "version": "0.2.0"}
