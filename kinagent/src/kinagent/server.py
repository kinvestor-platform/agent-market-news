import asyncio
import json
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from kinagent.agent import BaseAgent
from kinagent.bootstrap import bootstrap_from_marketplace
from kinagent.heartbeat import heartbeat_loop

logger = structlog.get_logger()


class RunRequest(BaseModel):
    model_config = {"extra": "allow"}


def _load_manifest() -> dict | None:
    for candidate in ["agent.manifest.json", "/app/agent.manifest.json"]:
        p = Path(candidate)
        if p.exists():
            return json.loads(p.read_text())
    return None


def _build_app(agent: BaseAgent) -> FastAPI:
    app = FastAPI(title=f"kinagent-{agent.agent_type}")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "agent_id": agent.agent_id, "agent_type": agent.agent_type}

    @app.post("/v1/run")
    async def run(request: RunRequest) -> JSONResponse:
        result = await agent.handle(request.model_dump())
        return JSONResponse(content=result)

    return app


async def run_agent(agent: BaseAgent, marketplace_url: str, port: int = 8000) -> None:
    manifest = _load_manifest()
    taxonomy = manifest.get("taxonomy", {}) if manifest else {}

    data = await bootstrap_from_marketplace(agent.agent_type, marketplace_url, taxonomy)
    agent.agent_id = data["agent_id"]
    agent.agent_secret = data["agent_secret"]
    agent.config = data["config"]
    agent.telemetry_url = data["telemetry_url"]
    agent.marketplace_url = marketplace_url

    asyncio.create_task(heartbeat_loop(agent.telemetry_url, port))

    app = _build_app(agent)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
