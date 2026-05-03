import structlog

logger = structlog.get_logger()


class LLMError(Exception):
    pass


class LLMRouter:
    def __init__(self, primary: str = "gemini-flash", fallback: str = "claude-haiku") -> None:
        self.primary = primary
        self.fallback = fallback

    async def chat(self, messages: list[dict], tools: list | None = None, max_tokens: int = 2000) -> str:
        if "gemini" in self.primary:
            try:
                from kinagent.llm.gemini import GeminiProvider
                return await GeminiProvider().chat(messages, tools, max_tokens)
            except Exception as e:
                logger.warning("gemini_failed", error=str(e), fallback=self.fallback)

        if "claude" in self.fallback or "anthropic" in self.fallback:
            try:
                from kinagent.llm.anthropic import AnthropicProvider
                return await AnthropicProvider().chat(messages, tools, max_tokens)
            except Exception as e:
                logger.error("anthropic_failed", error=str(e))

        raise LLMError("All LLM providers failed")
