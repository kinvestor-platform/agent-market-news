import asyncio
import importlib

import structlog

from kinagent.llm.base import (
    AuthError,
    BaseProvider,
    LLMError,
    ProviderResult,
    ProviderUnavailableError,
    RateLimitError,
    TokenLimitError,
)

logger = structlog.get_logger()

# keyword → (module, class)
_REGISTRY: dict[str, tuple[str, str]] = {
    "openai":    ("kinagent.llm.openai_compatible", "OpenAIProvider"),
    "gpt":       ("kinagent.llm.openai_compatible", "OpenAIProvider"),
    "groq":      ("kinagent.llm.openai_compatible", "GroqProvider"),
    "llama":     ("kinagent.llm.openai_compatible", "GroqProvider"),
    "ollama":    ("kinagent.llm.openai_compatible", "OllamaProvider"),
    "local":     ("kinagent.llm.openai_compatible", "OllamaProvider"),
    "deepseek":  ("kinagent.llm.openai_compatible", "DeepSeekProvider"),
    "gemini":    ("kinagent.llm.gemini",            "GeminiProvider"),
    "claude":    ("kinagent.llm.anthropic",         "AnthropicProvider"),
    "anthropic": ("kinagent.llm.anthropic",         "AnthropicProvider"),
    "haiku":     ("kinagent.llm.anthropic",         "AnthropicProvider"),
    "sonnet":    ("kinagent.llm.anthropic",         "AnthropicProvider"),
}

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.5  # seconds; doubles each retry


def _resolve(name: str) -> BaseProvider:
    key = name.lower()
    for keyword, (mod_path, cls_name) in _REGISTRY.items():
        if keyword in key:
            mod = importlib.import_module(mod_path)
            return getattr(mod, cls_name)()
    raise LLMError(f"Unknown provider '{name}'. Known: {', '.join(_REGISTRY)}")


class LLMRouter:
    """
    Routes chat requests through an ordered provider chain.

    - Tries providers in order: primary → fallbacks
    - Retries with exponential backoff on RateLimitError (up to _MAX_RETRIES)
    - Skips a provider on AuthError or ProviderUnavailableError
    - Raises TokenLimitError immediately (retrying won't help)
    - Returns ProviderResult with token counts for billing
    """

    def __init__(
        self,
        primary: str = "gemini",
        fallbacks: list[str] | None = None,
    ) -> None:
        # Accept old-style fallback= kwarg as well
        self._chain: list[str] = [primary] + (fallbacks or ["claude"])

    @classmethod
    def from_chain(cls, providers: list[str]) -> "LLMRouter":
        """Build a router from an explicit ordered list of provider names."""
        instance = cls.__new__(cls)
        instance._chain = providers
        return instance

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 2000,
    ) -> ProviderResult:
        last_error: Exception = LLMError("No providers in chain")

        for provider_name in self._chain:
            try:
                provider = _resolve(provider_name)
            except (LLMError, ProviderUnavailableError) as e:
                logger.warning("provider_unavailable", provider=provider_name, error=str(e))
                last_error = e
                continue

            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    result = await provider.chat(messages, tools, max_tokens)
                    if attempt > 1:
                        logger.info("llm_recovered", provider=provider.name, attempt=attempt)
                    return result

                except TokenLimitError:
                    raise  # no point retrying or failing over — request itself is too large

                except RateLimitError as e:
                    if attempt == _MAX_RETRIES:
                        logger.warning("rate_limit_exhausted", provider=provider.name)
                        last_error = e
                        break
                    wait = e.retry_after or (_BACKOFF_BASE ** attempt)
                    logger.warning("rate_limited", provider=provider.name, wait=wait, attempt=attempt)
                    await asyncio.sleep(wait)

                except (AuthError, ProviderUnavailableError) as e:
                    logger.warning("provider_skip", provider=provider.name, reason=str(e))
                    last_error = e
                    break  # skip to next provider — retrying won't fix auth

                except Exception as e:
                    if attempt == _MAX_RETRIES:
                        logger.error("provider_failed", provider=provider.name, error=str(e))
                        last_error = e
                        break
                    wait = _BACKOFF_BASE ** attempt
                    logger.warning("llm_error_retry", provider=provider.name, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)

        raise LLMError(f"All providers exhausted. Last error: {last_error}")
