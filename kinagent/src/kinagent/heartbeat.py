import asyncio
import os

import httpx
import structlog

logger = structlog.get_logger()


async def heartbeat_loop(telemetry_url: str, port: int) -> None:
    # AGENT_EXTERNAL_URL is injected by the platform (LoadBalancer IP or hostname).
    # Falls back to POD_IP (K8s downward API) then localhost for local dev.
    pod_ip = os.environ.get("POD_IP", "localhost")
    external = os.environ.get("AGENT_EXTERNAL_URL", f"http://{pod_ip}:{port}")
    while True:
        await asyncio.sleep(30)
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    telemetry_url,
                    json={"status": "idle", "tasks_completed": 0, "endpoint_url": external},
                )
        except Exception as e:
            logger.warning("heartbeat_failed", error=str(e))
