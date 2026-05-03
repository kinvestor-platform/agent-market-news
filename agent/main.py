import asyncio
import json
import os
import re

from kinagent import BaseAgent, run_agent
from kinagent.llm import LLMRouter
from kinagent.tools import fetch_url, web_search

from agent.prompts import SYSTEM_PROMPT


class MarketNewsAgent(BaseAgent):
    agent_type = "market_news"
    version = "0.1.0"

    def __init__(self) -> None:
        self.llm = LLMRouter(primary="gemini-flash", fallback="claude-haiku")
        self._tools = [web_search, fetch_url]

    async def handle(self, input: dict) -> dict:
        ticker = input.get("ticker", "AAPL").upper()
        days = input.get("days", 7)

        search_results = await web_search(f"{ticker} stock news last {days} days", max_results=5)

        articles: list[str] = []
        for result in search_results[:3]:
            try:
                content = await fetch_url(result["url"])
                articles.append(f"Source: {result['url']}\n{content[:1000]}")
            except Exception:
                pass

        context = "\n\n---\n\n".join(articles) if articles else "No articles found."

        messages = [
            {"role": "user", "content": f"""{SYSTEM_PROMPT}

Analyze recent news for {ticker} stock from the last {days} days.

News context:
{context}

Provide a JSON response with exactly this structure:
{{
  "ticker": "{ticker}",
  "summary": "2-3 sentence overall summary",
  "sentiment": "bullish" or "bearish" or "neutral",
  "key_points": ["point 1", "point 2", "point 3"],
  "sources": ["url1", "url2"]
}}

Return ONLY the JSON, no other text."""}
        ]

        response_text = await self.llm.chat(messages, max_tokens=1000)

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "ticker": ticker,
            "summary": response_text[:500],
            "sentiment": "neutral",
            "key_points": [],
            "sources": [r["url"] for r in search_results[:3]],
        }


if __name__ == "__main__":
    agent = MarketNewsAgent()
    marketplace_url = os.environ.get(
        "MARKETPLACE_URL",
        "https://marketplace-placeholder-uc.a.run.app",
    )
    asyncio.run(run_agent(agent, marketplace_url=marketplace_url, port=8000))
