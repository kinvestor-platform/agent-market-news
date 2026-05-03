from urllib.parse import quote

import httpx

from kinagent.tools.base import tool


@tool(name="web_search", description="Search the web and return top results")
async def web_search(query: str, max_results: int = 5) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; kinagent/1.0)"}
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)

    results: list[dict] = []
    # Parse the HTML response for result links
    import re
    # DDG HTML returns results in anchor tags with class "result__a"
    pattern = re.compile(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<',
        re.IGNORECASE,
    )
    for m in pattern.finditer(response.text):
        url_raw, title = m.group(1), m.group(2).strip()
        # DDG wraps URLs — decode the actual URL
        if "uddg=" in url_raw:
            from urllib.parse import unquote, urlparse, parse_qs
            params = parse_qs(urlparse(url_raw).query)
            actual = params.get("uddg", [url_raw])[0]
            url_raw = unquote(actual)
        if url_raw.startswith("http") and len(results) < max_results:
            results.append({"title": title[:120], "url": url_raw})
    return results
