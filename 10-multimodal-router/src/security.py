import os
import hmac
import hashlib
from fastapi import Request, HTTPException

SHARED = os.getenv("SUITE_SHARED_SECRET")


async def verify_sig(request: Request, body: bytes):
    """Optional HMAC verification for JSON POSTs. No-op if env var not set."""
    if not SHARED:
        return
    sig = request.headers.get("X-SUITE-SIG", "")
    mac = hmac.new(SHARED.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, mac):
        raise HTTPException(status_code=401, detail="bad signature")
