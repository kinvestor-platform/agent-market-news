import os


class GeminiProvider:
    def __init__(self) -> None:
        self.project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
        self.location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

    async def chat(self, messages: list[dict], tools: list | None = None, max_tokens: int = 2000) -> str:
        from google import genai
        from google.genai import types

        # Prefer API key if set; fall back to Vertex AI via ADC
        if self.api_key:
            client = genai.Client(api_key=self.api_key)
        elif self.project:
            client = genai.Client(vertexai=True, project=self.project, location=self.location)
        else:
            raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT")

        prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text
