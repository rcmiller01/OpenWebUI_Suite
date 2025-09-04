"""
Drive State Service
Simulates user mood/needs with bounded random walk and event reactions
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uvicorn

from drive_state import drive_manager, DriveState


class UpdateRequest(BaseModel):
    """Request model for updating drive state"""
    delta: Dict[str, float] = Field(..., description="Drive deltas to apply")
    reason: str = Field("", description="Reason for the update")


class DriveStateResponse(BaseModel):
    """Response model for drive state"""
    user_id: str
    energy: float
    sociability: float
    curiosity: float
    empathy_reserve: float
    novelty_seek: float
    timestamp: float


class PolicyResponse(BaseModel):
    """Response model for style policy"""
    energy_level: str
    social_style: str
    curiosity_level: str
    empathy_approach: str
    novelty_preference: str
    style_hints: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Drive State Service starting...")
    yield
    # Shutdown
    print("Drive State Service shutting down...")


app = FastAPI(
    title="Drive State Service",
    description="User mood/needs simulation with bounded random walk",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "drive-state"}


@app.get("/drive/get", response_model=DriveStateResponse)
async def get_drive_state(user_id: str = Query(..., description="User ID")):
    """Get current drive state for user"""
    try:
        state = drive_manager.get_drive_state(user_id)
        return DriveStateResponse(**state.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drive state: {str(e)}")


@app.post("/drive/update", response_model=DriveStateResponse)
async def update_drive_state(request: UpdateRequest,
                           user_id: str = Query(..., description="User ID")):
    """Update drive state with deltas"""
    try:
        # Validate delta values
        for drive, delta in request.delta.items():
            if drive not in ['energy', 'sociability', 'curiosity', 'empathy_reserve', 'novelty_seek']:
                raise HTTPException(status_code=400, detail=f"Invalid drive: {drive}")
            if not isinstance(delta, (int, float)):
                raise HTTPException(status_code=400, detail=f"Delta must be numeric: {drive}")

        state = drive_manager.update_drive_state(user_id, request.delta, request.reason)
        return DriveStateResponse(**state.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update drive state: {str(e)}")


@app.post("/drive/policy", response_model=PolicyResponse)
async def get_style_policy(user_id: str = Query(..., description="User ID")):
    """Get style policy based on current drive state"""
    try:
        policy = drive_manager.get_style_policy(user_id)
        return PolicyResponse(**policy)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get style policy: {str(e)}")


@app.get("/drive/history")
async def get_drive_history(user_id: str = Query(..., description="User ID"),
                          limit: int = Query(10, description="Number of recent states to return")):
    """Get recent drive state history (simplified - returns current state)"""
    try:
        state = drive_manager.get_drive_state(user_id)
        return {
            "user_id": user_id,
            "current_state": state.to_dict(),
            "history_limit": limit,
            "note": "Full history tracking not implemented - returns current state"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drive history: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8105)
