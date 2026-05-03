from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# ── Errors ────────────────────────────────────────────────────────────────────

class LLMError(Exception):
    """Base for all LLM errors."""

class AuthError(LLMError):
    """Bad or missing API key."""

class RateLimitError(LLMError):
    """Provider returned 429 — retry after backoff."""
    def __init__(self, msg: str = "", retry_after: float | None = None):
        super().__init__(msg)
        self.retry_after = retry_after  # seconds, if provided by header

class TokenLimitError(LLMError):
    """Request exceeds model context window."""

class ProviderUnavailableError(LLMError):
    """Provider is down, unreachable, or not configured."""


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class ProviderResult:
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# ── Base ──────────────────────────────────────────────────────────────────────

class BaseProvider(ABC):
    """
    All LLM providers implement this interface.

    messages format follows OpenAI convention:
        [{"role": "system"|"user"|"assistant", "content": "..."}]

    tools format follows OpenAI function-calling spec:
        [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short provider identifier e.g. 'openai', 'groq', 'ollama'."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Active model name."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 2000,
    ) -> ProviderResult:
        """Send messages, return structured result with token counts."""
