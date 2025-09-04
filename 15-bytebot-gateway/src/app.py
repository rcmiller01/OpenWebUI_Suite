"""
ByteBot Gateway Service
Safe interface for ByteBot desktop automation
"""

import os
import uuid
import hmac
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import BaseModel

from .adapters.bytebot_http import plan as bb_plan, execute as bb_exec


# Configuration
class Settings(BaseModel):
    """Application settings"""
    bytebot_url: str = os.getenv("BYTEBOT_URL", "http://localhost:9000")
    bytebot_internal_key: str = os.getenv("BYTEBOT_INTERNAL_KEY", "dev")
    shared_secret: str = os.getenv("BYTEBOT_SHARED_SECRET", "dev")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8100"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    workdir: str = os.getenv("WORKDIR", "/tmp/bytebot-gateway")


settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models
class PlanRequest(BaseModel):
    """Request model for planning actions"""
    intent: str
    args: Dict[str, Any] = {}


class ExecuteRequest(PlanRequest):
    """Request model for executing actions"""
    task_id: str
    confirm_token: str


class PlanResponse(BaseModel):
    """Response model for plan operations"""
    task_id: str
    plan: List[str]
    est_risk: str
    confirm_token: str


class ExecuteResponse(BaseModel):
    """Response model for execute operations"""
    status: str
    observations: List[str] = []
    artifacts: List[Dict[str, Any]] = []


class CapabilitiesResponse(BaseModel):
    """Response model for capabilities"""
    caps: List[str]
    limits: Dict[str, Any]


class HealthResponse(BaseModel):
    """Response model for health checks"""
    status: str
    version: str = "1.0.0"
    timestamp: str


# Global state
active_tasks: Dict[str, Dict[str, Any]] = {}
task_events: Dict[str, List[Dict[str, Any]]] = {}


def verify_signature(signature: str, body: bytes) -> None:
    """Verify HMAC signature"""
    expected = hmac.new(
        settings.shared_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature or "", expected):
        raise HTTPException(status_code=401, detail="Invalid signature")


def generate_confirm_token(task_id: str) -> str:
    """Generate confirmation token for task"""
    return hmac.new(
        settings.shared_secret.encode(),
        task_id.encode(),
        hashlib.sha256
    ).hexdigest()


def validate_capability(intent: str) -> bool:
    """Validate if capability is allowed"""
    # TODO: Load from policy.json
    allowed_caps = [
        "fs.read", "fs.write", "browser", "shell",
        "screenshot", "open_app", "edit_file", "run"
    ]
    return intent in allowed_caps


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting ByteBot Gateway Service")
    logger.info(f"ByteBot URL: {settings.bytebot_url}")
    logger.info(f"Host: {settings.host}:{settings.port}")

    # Create work directory
    os.makedirs(settings.workdir, exist_ok=True)

    yield

    logger.info("Shutting down ByteBot Gateway Service")


# FastAPI app
app = FastAPI(
    title="ByteBot Gateway",
    description="Safe interface for ByteBot desktop automation",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    """Get available capabilities and limits"""
    return CapabilitiesResponse(
        caps=[
            "fs.read", "fs.write", "browser", "shell",
            "screenshot", "open_app", "edit_file", "run"
        ],
        limits={
            "timeout_s": 60,
            "max_file_size": 10485760,
            "rate_limit_per_minute": 10
        }
    )


@app.post("/plan", response_model=PlanResponse)
async def plan_action(
    request: Request,
    x_bytebot_sig: str = Header(default="")
):
    """Plan a ByteBot action (dry-run)"""
    try:
        # Get and verify request body
        body = await request.body()
        verify_signature(x_bytebot_sig, body)

        # Parse request
        data = PlanRequest.model_validate_json(body)

        # Validate capability
        if not validate_capability(data.intent):
            raise HTTPException(
                status_code=403,
                detail=f"Capability '{data.intent}' not allowed"
            )

        logger.info(f"Planning action: {data.intent}")

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Plan the action
        plan_result = await bb_plan(data.intent, data.args)

        # Store task info
        active_tasks[task_id] = {
            "intent": data.intent,
            "args": data.args,
            "plan": plan_result.get("plan", []),
            "risk": plan_result.get("risk", "low"),
            "created_at": datetime.utcnow().isoformat()
        }

        # Initialize events
        task_events[task_id] = [{
            "event": "task_created",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"task_id": task_id, "intent": data.intent}
        }]

        # Generate confirm token
        confirm_token = generate_confirm_token(task_id)

        return PlanResponse(
            task_id=task_id,
            plan=plan_result.get("plan", []),
            est_risk=plan_result.get("risk", "low"),
            confirm_token=confirm_token
        )

    except Exception as e:
        logger.error(f"Plan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute", response_model=ExecuteResponse)
async def execute_action(
    request: Request,
    x_bytebot_sig: str = Header(default="")
):
    """Execute a planned ByteBot action"""
    try:
        # Get and verify request body
        body = await request.body()
        verify_signature(x_bytebot_sig, body)

        # Parse request
        data = ExecuteRequest.model_validate_json(body)

        # Validate task exists
        if data.task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        # Validate confirm token
        expected_token = generate_confirm_token(data.task_id)
        if data.confirm_token != expected_token:
            raise HTTPException(
                status_code=403,
                detail="Invalid confirm token"
            )

        logger.info(f"Executing action: {data.intent} (task: {data.task_id})")

        # Add execution event
        task_events[data.task_id].append({
            "event": "task_executing",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"task_id": data.task_id}
        })

        # Execute the action
        result = await bb_exec(
            data.task_id,
            data.intent,
            data.args,
            data.confirm_token
        )

        # Add completion event
        task_events[data.task_id].append({
            "event": "task_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "task_id": data.task_id,
                "status": result.get("status", "unknown")
            }
        })

        # Clean up task after execution
        del active_tasks[data.task_id]

        return ExecuteResponse(
            status=result.get("status", "unknown"),
            observations=result.get("observations", []),
            artifacts=result.get("artifacts", [])
        )

    except Exception as e:
        logger.error(f"Execute failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events")
async def get_events(task_id: str = Query(..., description="Task ID")):
    """Get event stream for a task (SSE)"""
    if task_id not in task_events:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        """Generate SSE events"""
        events = task_events[task_id]
        for event in events:
            yield f"data: {event}\n\n"
            await asyncio.sleep(0.1)  # Small delay between events

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
