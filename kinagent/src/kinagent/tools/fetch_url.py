import re

import httpx

from kinagent.tools.base import tool


@tool(name="fetch_url", description="Fetch the text content of a URL")
async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        response = await client.get(url, headers={"User-Agent": "kinagent/0.2"})
        text = re.sub(r"<[^>]+>", " ", response.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000]
