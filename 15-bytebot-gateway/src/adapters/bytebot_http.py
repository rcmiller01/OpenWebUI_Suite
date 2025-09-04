"""
ByteBot HTTP Adapter
Communicates with ByteBot's REST API
"""

import httpx
import os
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ByteBotAdapter:
    """Adapter for communicating with ByteBot API"""

    def __init__(self):
        self.base_url = os.getenv("BYTEBOT_URL", "http://localhost:9000")
        self.internal_key = os.getenv("BYTEBOT_INTERNAL_KEY", "dev")
        self.timeout_plan = int(os.getenv("BYTEBOT_TIMEOUT_PLAN", "30"))
        self.timeout_execute = int(os.getenv("BYTEBOT_TIMEOUT_EXECUTE", "120"))
        self.retry_attempts = int(os.getenv("BYTEBOT_RETRY_ATTEMPTS", "3"))
        self.retry_delay = float(os.getenv("BYTEBOT_RETRY_DELAY", "1.0"))

        # HTTP client session
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_plan, connect=10.0),
            headers={"X-KEY": self.internal_key}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _make_request(self, method: str, endpoint: str,
                           json_data: Optional[Dict] = None,
                           timeout: Optional[float] = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        if not self._client:
            async with self:
                return await self._make_request(
                    method, endpoint, json_data, timeout
                )

        url = f"{self.base_url}{endpoint}"
        timeout_config = httpx.Timeout(
            timeout or self.timeout_plan, connect=10.0
        )

        for attempt in range(self.retry_attempts):
            try:
                response = await self._client.request(
                    method, url, json=json_data, timeout=timeout_config
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if (e.response.status_code >= 500 and
                        attempt < self.retry_attempts - 1):
                    logger.warning(
                        f"Server error (attempt {attempt + 1}): {e}"
                    )
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}): {e}"
                    )
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

        raise Exception(f"Failed after {self.retry_attempts} attempts")

    async def plan(self, intent: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plan for the given intent and arguments"""
        logger.info(
            f"Planning action: {intent}",
            extra={"intent": intent, "args": args}
        )

        try:
            result = await self._make_request(
                "POST", "/plan",
                json_data={"intent": intent, "args": args}
            )

            logger.info("Plan created successfully", extra={
                "intent": intent,
                "plan_steps": len(result.get("plan", [])),
                "risk_level": result.get("risk", "unknown")
            })

            return result

        except Exception as e:
            logger.error(f"Failed to create plan for {intent}: {e}")
            # Return a default plan structure on error
            return {
                "plan": [f"Execute {intent} with provided arguments"],
                "risk": "high",
                "error": str(e)
            }

    async def execute(self, task_id: str, intent: str, args: Dict[str, Any],
                     confirm_token: str) -> Dict[str, Any]:
        """Execute a planned action"""
        logger.info(f"Executing action: {intent}", extra={
            "task_id": task_id,
            "intent": intent
        })

        try:
            result = await self._make_request(
                "POST", "/execute",
                json_data={
                    "task_id": task_id,
                    "intent": intent,
                    "args": args,
                    "confirm_token": confirm_token
                },
                timeout=self.timeout_execute
            )

            logger.info("Action executed successfully", extra={
                "task_id": task_id,
                "intent": intent,
                "status": result.get("status", "unknown"),
                "artifacts_count": len(result.get("artifacts", []))
            })

            return result

        except Exception as e:
            logger.error(f"Failed to execute {intent} (task {task_id}): {e}")
            return {
                "status": "error",
                "error": str(e),
                "observations": [f"Execution failed: {e}"],
                "artifacts": []
            }

    async def health_check(self) -> Dict[str, Any]:
        """Check ByteBot service health"""
        try:
            result = await self._make_request("GET", "/health")
            return {"status": "healthy", "details": result}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get ByteBot capabilities"""
        try:
            result = await self._make_request("GET", "/capabilities")
            return result
        except Exception as e:
            logger.error(f"Failed to get capabilities: {e}")
            return {"capabilities": [], "error": str(e)}


# Global adapter instance
_adapter: Optional[ByteBotAdapter] = None


async def get_adapter() -> ByteBotAdapter:
    """Get or create adapter instance"""
    global _adapter
    if _adapter is None:
        _adapter = ByteBotAdapter()
    return _adapter


async def plan(intent: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Plan a ByteBot action"""
    adapter = await get_adapter()
    async with adapter:
        return await adapter.plan(intent, args)


async def execute(task_id: str, intent: str, args: Dict[str, Any],
                 confirm_token: str) -> Dict[str, Any]:
    """Execute a ByteBot action"""
    adapter = await get_adapter()
    async with adapter:
        return await adapter.execute(task_id, intent, args, confirm_token)
