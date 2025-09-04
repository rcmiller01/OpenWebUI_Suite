# ByteBot Gateway

## Goal

Expose ByteBot as a safe "super-tool" for Open WebUI/Pipelines:
**plan → confirm → execute**, with artifacts + live event stream.

## API

- `GET  /capabilities` → `{ caps:[...], limits:{...} }`
- `POST /plan`        → `{ task_id, plan, est_risk, confirm_token }`
- `POST /execute`     → `{ status, observations[], artifacts[] }`
- `GET  /events?task_id=...` (SSE/WS) → log stream

## Security

- HMAC signature header `X-BYTEBOT-SIG`
- Capability allow-list (`config/policy.json`)
- Sandbox workdir; non-root user

## Run

```bash
uv pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8100

Test
curl -s http://localhost:8100/capabilities
curl -s -X POST :8100/plan -H "X-BYTEBOT-SIG: <sig>" -d '{"intent":"screenshot","args":{"window":"desktop"}}'
```

## Minimal files

```text
01-bytebot-gateway/
Dockerfile
requirements.txt
config/
policy.json # capability allow-list
bytebot.json # adapter config (url, tokens)
src/
app.py # FastAPI with /capabilities /plan /execute /events
adapters/
bytebot_http.py # talks to ByteBot's API
bytebot_cli.py # optional CLI wrapper
```

**`src/app.py` (starter):**

```python
from fastapi import FastAPI, Header, HTTPException, Request
import os, time, uuid, hmac, hashlib
from pydantic import BaseModel
from typing import Dict, Any
from .adapters.bytebot_http import plan as bb_plan, execute as bb_exec

SECRET = os.getenv("BYTEBOT_SHARED_SECRET","dev")
def check_sig(sig: str, body: bytes):
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig or "", mac): raise HTTPException(401, "bad sig")

app = FastAPI()

@app.get("/capabilities")
async def caps():
    return {"caps":["fs.read","fs.write","browser","shell","screenshot"],
            "limits":{"timeout_s":60}}

class PlanIn(BaseModel):
    intent: str
    args: Dict[str, Any] = {}

@app.post("/plan")
async def plan(req: Request, x_bytebot_sig: str = Header(default="")):
    body = await req.body(); check_sig(x_bytebot_sig, body)
    data = PlanIn.model_validate_json(body)
    tid = str(uuid.uuid4())
    p = await bb_plan(data.intent, data.args)
    return {"task_id": tid, "plan": p.get("plan", []), "est_risk": p.get("risk","low"),
            "confirm_token": hmac.new(SECRET.encode(), tid.encode(), hashlib.sha256).hexdigest()}

class ExecIn(PlanIn):
    task_id: str
    confirm_token: str

@app.post("/execute")
async def execute(req: Request, x_bytebot_sig: str = Header(default="")):
    body = await req.body(); check_sig(x_bytebot_sig, body)
    data = ExecIn.model_validate_json(body)
    tok = hmac.new(SECRET.encode(), data.task_id.encode(), hashlib.sha256).hexdigest()
    if tok != data.confirm_token: raise HTTPException(403, "bad confirm token")
    res = await bb_exec(data.task_id, data.intent, data.args, data.confirm_token)
    return res
```

## src/adapters/bytebot_http.py (stub)

```python
import httpx, os
BASE = os.getenv("BYTEBOT_URL","http://localhost:9000")
KEY  = os.getenv("BYTEBOT_INTERNAL_KEY","dev")

async def plan(intent, args):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/plan", json={"intent":intent,"args":args},
                         headers={"X-KEY":KEY}); r.raise_for_status(); return r.json()

async def execute(task_id, intent, args, confirm_token):
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{BASE}/execute", json={
            "task_id":task_id,"intent":intent,"args":args,"confirm_token":confirm_token
        }, headers={"X-KEY":KEY}); r.raise_for_status(); return r.json()
```

## Wire it into your 00-pipelines-gateway

### 1) Add tools to 00-pipelines-gateway/config/tools.json

Append these two entries under "external_tools":

```json
{
  "name": "bytebot_plan",
  "description": "Plan a desktop action via ByteBot (dry-run).",
  "module": "tools.bytebot",
  "enabled": true,
  "parameters": {
    "type": "object",
    "properties": {
      "intent": { "type": "string", "enum": ["open_app","browse","edit_file","screenshot","run"] },
      "args": { "type": "object" }
    },
    "required": ["intent","args"]
  }
},
{
  "name": "bytebot_execute",
  "description": "Execute a previously planned ByteBot action after confirmation.",
  "module": "tools.bytebot",
  "enabled": true,
  "parameters": {
    "type": "object",
    "properties": {
      "task_id": { "type": "string" },
      "intent":  { "type": "string" },
      "args":    { "type": "object" },
      "confirm_token": { "type": "string" }
    },
    "required": ["task_id","intent","args","confirm_token"]
  }
}
```

### 2) Minimal tool handler in 00-pipelines-gateway/src/tools/registry.py

Add a bytebot tool module:

```python
# src/tools/bytebot.py
import os, hmac, hashlib, httpx, json

GATEWAY = os.getenv("BYTEBOT_GATEWAY_URL","http://bytebot-vm:8100")
SECRET  = os.getenv("BYTEBOT_SHARED_SECRET","dev")

def _sig(payload: dict)->dict:
    raw = json.dumps(payload,separators=(",",":")).encode()
    mac = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return {"headers":{"X-BYTEBOT-SIG":mac}, "raw":raw}

async def bytebot_plan(intent:str, args:dict):
    payload = {"intent":intent,"args":args}; sig = _sig(payload)
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{GATEWAY}/plan", content=sig["raw"], headers=sig["headers"]); r.raise_for_status()
        return r.json()

async def bytebot_execute(task_id:str, intent:str, args:dict, confirm_token:str):
    payload = {"task_id":task_id,"intent":intent,"args":args,"confirm_token":confirm_token}; sig = _sig(payload)
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{GATEWAY}/execute", content=sig["raw"], headers=sig["headers"]); r.raise_for_status()
        return r.json()
```

### 3) Policy in your pipeline (pre-merge hook)

On any model request to bytebot_plan, always:

call /plan via the tool,

present the plan to you in chat (bullets + risk),

wait for explicit "Approve",

then call bytebot_execute with the task_id + confirm_token
