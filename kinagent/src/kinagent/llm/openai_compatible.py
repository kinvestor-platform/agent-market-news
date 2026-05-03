import os

from openai import AsyncOpenAI, APIStatusError, AuthenticationError, RateLimitError as OpenAIRateLimit

from kinagent.llm.base import (
    AuthError,
    BaseProvider,
    LLMError,
    ProviderResult,
    ProviderUnavailableError,
    RateLimitError,
    TokenLimitError,
)


class OpenAICompatibleProvider(BaseProvider):
    """
    Base for all OpenAI-compatible APIs: OpenAI, Groq, Ollama, DeepSeek.
    Subclasses override class-level defaults; env vars override those at runtime.
    """

    _base_url: str | None = None
    _default_model: str = "gpt-4o-mini"
    _api_key_env: str = "OPENAI_API_KEY"
    _api_key_fallback: str | None = None   # for providers that don't need a real key (Ollama)
    _provider_name: str = "openai"

    def __init__(self) -> None:
        api_key = os.environ.get(self._api_key_env) or self._api_key_fallback
        if not api_key:
            raise ProviderUnavailableError(f"{self._api_key_env} not set")
        self._model = os.environ.get(f"{self._provider_name.upper()}_MODEL", self._default_model)
        self._client = AsyncOpenAI(api_key=api_key, base_url=self._get_base_url())

    def _get_base_url(self) -> str | None:
        return self._base_url

    @property
    def name(self) -> str:
        return self._provider_name

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
            kwargs: dict = dict(model=self._model, messages=messages, max_tokens=max_tokens)
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**kwargs)
            usage = response.usage

            return ProviderResult(
                content=response.choices[0].message.content or "",
                provider=self._provider_name,
                model=self._model,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

        except AuthenticationError as e:
            raise AuthError(str(e)) from e
        except OpenAIRateLimit as e:
            retry = None
            if hasattr(e, "response") and e.response:
                retry_header = e.response.headers.get("retry-after")
                retry = float(retry_header) if retry_header else None
            raise RateLimitError(str(e), retry_after=retry) from e
        except APIStatusError as e:
            if e.status_code == 400 and "context" in str(e).lower():
                raise TokenLimitError(str(e)) from e
            raise LLMError(str(e)) from e


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI — GPT-4o-mini default. Env: OPENAI_API_KEY, OPENAI_MODEL."""
    _provider_name = "openai"
    _api_key_env = "OPENAI_API_KEY"
    _default_model = "gpt-4o-mini"


class GroqProvider(OpenAICompatibleProvider):
    """Groq — fast inference. Env: GROQ_API_KEY, GROQ_MODEL."""
    _provider_name = "groq"
    _base_url = "https://api.groq.com/openai/v1"
    _api_key_env = "GROQ_API_KEY"
    _default_model = "llama-3.1-8b-instant"


class OllamaProvider(OpenAICompatibleProvider):
    """
    Ollama — local models, no API key needed.
    Env: OLLAMA_BASE_URL (default: http://localhost:11434/v1), OLLAMA_MODEL (default: llama3.2).
    """
    _provider_name = "ollama"
    _api_key_env = "OLLAMA_API_KEY"
    _api_key_fallback = "ollama"          # openai SDK requires a non-empty string
    _default_model = "llama3.2"

    def _get_base_url(self) -> str:
        return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek — cloud API, OpenAI-compatible. Env: DEEPSEEK_API_KEY, DEEPSEEK_MODEL."""
    _provider_name = "deepseek"
    _base_url = "https://api.deepseek.com"
    _api_key_env = "DEEPSEEK_API_KEY"
    _default_model = "deepseek-chat"
