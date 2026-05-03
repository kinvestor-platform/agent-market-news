# agent-market-news

Market news summarizer agent for the Kinvestor Agent Platform.

## What it does

Given a stock ticker, fetches recent news via web search and summarizes it using Gemini Flash (with Claude Haiku fallback).

**Input:**
```json
{"ticker": "AAPL", "days": 7}
```

**Output:**
```json
{
  "ticker": "AAPL",
  "summary": "Apple Inc. has seen...",
  "sentiment": "bullish",
  "key_points": ["...", "...", "..."],
  "sources": ["https://..."]
}
```

## Local dev

```bash
pip install kinagent
MARKETPLACE_URL=http://localhost:7777 GEMINI_API_KEY=your-key python -m agent.main
```

## Deploy

See `k8s/deployment.yaml`. Requires:
- `kinvestor-platform/agent-marketplace` running on Cloud Run
- `agent-secrets` K8s secret with `gemini-api-key`
