import os

import anthropic as anthropic_sdk


class AnthropicProvider:
    def __init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic_sdk.Anthropic(api_key=api_key)

    async def chat(self, messages: list[dict], tools: list | None = None, max_tokens: int = 2000) -> str:
        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.content[0].text  # type: ignore[union-attr]
