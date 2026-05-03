import os

from kinagent.llm.base import (
    AuthError,
    BaseProvider,
    LLMError,
    ProviderResult,
    ProviderUnavailableError,
    RateLimitError,
)


class GeminiProvider(BaseProvider):
    """
    Google Gemini via google-genai SDK.
    Env: GEMINI_API_KEY (API key mode) or GOOGLE_CLOUD_PROJECT (Vertex AI mode).
    Model: GEMINI_MODEL (default: gemini-2.0-flash-lite).
    """

    def __init__(self) -> None:
        self._api_key = os.environ.get("GEMINI_API_KEY")
        self._project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
        self._location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        self._model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

        if not self._api_key and not self._project:
            raise ProviderUnavailableError("Set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT")

    @property
    def name(self) -> str:
        return "gemini"

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
            from google import genai
            from google.genai import types
            from google.api_core.exceptions import ResourceExhausted, PermissionDenied

            if self._api_key:
                client = genai.Client(api_key=self._api_key)
            else:
                client = genai.Client(vertexai=True, project=self._project, location=self._location)

            prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens),
            )

            usage = response.usage_metadata
            return ProviderResult(
                content=response.text or "",
                provider="gemini",
                model=self._model,
                input_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
                output_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
            )

        except Exception as e:
            err = str(e).lower()
            if "quota" in err or "resource exhausted" in err or "429" in err:
                raise RateLimitError(str(e)) from e
            if "permission" in err or "unauthenticated" in err or "api key" in err:
                raise AuthError(str(e)) from e
            raise LLMError(str(e)) from e
