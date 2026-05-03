import os

import anthropic as anthropic_sdk

from kinagent.llm.base import (
    AuthError,
    BaseProvider,
    LLMError,
    ProviderResult,
    ProviderUnavailableError,
    RateLimitError,
    TokenLimitError,
)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude. Env: ANTHROPIC_API_KEY, ANTHROPIC_MODEL."""

    _default_model = "claude-haiku-4-5-20251001"

    def __init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY not set")
        self._model = os.environ.get("ANTHROPIC_MODEL", self._default_model)
        self._client = anthropic_sdk.AsyncAnthropic(api_key=api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 2000,
    ) -> ProviderResult:
        try:
            # Anthropic separates system messages from the messages list
            system = ""
            filtered = []
            for m in messages:
                if m["role"] == "system":
                    system = m["content"]
                else:
                    filtered.append(m)

            kwargs: dict = dict(
                model=self._model,
                max_tokens=max_tokens,
                messages=filtered,
            )
            if system:
                kwargs["system"] = system
            if tools:
                kwargs["tools"] = [
                    {
                        "name": t["function"]["name"],
                        "description": t["function"].get("description", ""),
                        "input_schema": t["function"].get("parameters", {}),
                    }
                    for t in tools
                ]

            response = await self._client.messages.create(**kwargs)
            content = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return ProviderResult(
                content=content,
                provider="anthropic",
                model=self._model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        except anthropic_sdk.AuthenticationError as e:
            raise AuthError(str(e)) from e
        except anthropic_sdk.RateLimitError as e:
            raise RateLimitError(str(e)) from e
        except anthropic_sdk.BadRequestError as e:
            if "too long" in str(e).lower() or "context" in str(e).lower():
                raise TokenLimitError(str(e)) from e
            raise LLMError(str(e)) from e
