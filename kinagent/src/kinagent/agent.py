from abc import ABC, abstractmethod


class BaseAgent(ABC):
    agent_type: str = ""
    version: str = "0.1.0"

    # Injected after bootstrap
    agent_id: str = ""
    agent_secret: str = ""
    config: dict = {}
    telemetry_url: str = ""
    marketplace_url: str = ""

    _tools: list = []

    @abstractmethod
    async def handle(self, input: dict) -> dict:
        pass

    def tools(self) -> list:
        return self._tools or []
