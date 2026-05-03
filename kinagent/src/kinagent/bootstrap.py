import os
from uuid import uuid4

import httpx
import structlog

logger = structlog.get_logger()


async def bootstrap_from_marketplace(
    agent_type: str,
    marketplace_url: str,
    taxonomy: dict | None = None,
) -> dict:
    pod_uid = os.environ.get("POD_UID", str(uuid4()))
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{marketplace_url}/v1/agents/bootstrap",
            json={
                "agent_type": agent_type,
                "pod_uid": pod_uid,
                "taxonomy": taxonomy or {},
            },
        )
        response.raise_for_status()
    data = response.json()
    logger.info("bootstrapped", agent_id=data["agent_id"], agent_type=agent_type)
    return data
