from __future__ import annotations
import re
import requests
from typing import Dict, Any, List
import config

_WIKIPEDIA_PATTERNS = [
    r"\b(history of|sejarah|kisah)\b",
    r"\b(who (is|was)|siapakah)\b",
    r"\b(when did|kapan)\b",
    r"\b(biography of|biografi)\b",
    r"\b(battle of|pertempuran|perang)\b",
    r"event", "figure", "person", "prophet", "sahabah"
]

def _route_query(query: str) -> str:
    """Routes query to either Wikipedia or SearxNG based on improved patterns."""
    q = (query or "").lower()
    if any(re.search(pat, q, re.IGNORECASE) for pat in _WIKIPEDIA_PATTERNS):
        return "wikipedia"
    return "searxng"

def _trim_text(s: str, limit: int = 400) -> str:
    s = (s or "").strip()
    return s if len(s) <= limit else s[:limit - 1] + "…"

def wikipedia_search(query: str, num: int = 2) -> List[Dict[str, Any]]:
    """Queries MediaWiki API and returns a list of normalized results."""
    lang = config.WIKIPEDIA_LANG
    headers = {'User-Agent': 'IslamicQnA-Agent/1.1'}
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "utf8": 1, "format": "json"},
            timeout=8, headers=headers
        )
        r.raise_for_status()
        data = r.json()
        hits = (data.get("query", {}).get("search", []))[:num]
        normalized = []
        for h in hits:
            title = h.get("title", "")
            url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
            snippet = re.sub('<[^<]+?>', '', h.get("snippet", "")) # Strip HTML tags
            normalized.append({"title": title, "url": url, "snippet": _trim_text(snippet), "provider": "wikipedia"})
        return normalized
    except requests.exceptions.RequestException as e:
        print(f"Wikipedia search failed: {e}")
        return []

def searxng_search(query: str, num: int = 3) -> List[Dict[str, Any]]:
    """Queries the self-hosted SearxNG API and returns a list of normalized results."""
    headers = {"Accept": "application/json"}
    params = {"q": query, "format": "json", "engines": config.SEARXNG_ENGINES, "language": config.WIKIPEDIA_LANG}
    try:
        # Using POST can sometimes be more reliable
        r = requests.post(config.SEARXNG_ENDPOINT, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = (data.get("results", []))[:num]
        return [{"title": _trim_text(it.get("title")), "url": it.get("url", ""), "snippet": _trim_text(it.get("content")), "provider": "searxng"} for it in results]
    except requests.exceptions.RequestException as e:
        print(f"SearxNG search failed: {e}")
        return []

def unified_search(query: str) -> Dict[str, Any]:
    """
    Performs a tiered web search and returns a dictionary of results.
    This is the main function called by the agent's tool.
    """
    print(f"Performing unified search for: {query}")
    route = _route_query(query)
    web_results = []
    if route == "wikipedia":
        web_results = wikipedia_search(query)
        if not web_results:
            web_results = searxng_search(query) # Fallback
    else: # Default to SearxNG
        web_results = searxng_search(query)
        if not web_results:
            web_results = wikipedia_search(query) # Fallback
            
    print(f"Found {len(web_results)} web results.")
    return {"web_results": web_results}