"""
LOVE Internet Access Layer

LOVE can search the web, read pages, fetch news, research topics,
and pull real-time data autonomously — triggered by conversation need
or by the idle mind during quiet hours.

Uses: DuckDuckGo (no key), requests + BeautifulSoup for page reading,
      feedparser for RSS news, with local cache to avoid re-fetching.
"""

import re
import json
import hashlib
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus, urlparse

PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "internet_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_COOLDOWN = 2.0  # seconds between searches
_last_search_time = 0
_lock = threading.Lock()


# ── Cache ────────────────────────────────────────────────────────────────────

def _cache_key(query: str) -> str:
    return hashlib.md5(query.encode()).hexdigest()[:16]


def _cache_get(key: str, max_age_minutes: int = 30) -> Optional[Any]:
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        if time.time() - mtime > max_age_minutes * 60:
            return None
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _cache_set(key: str, data: Any):
    try:
        with open(CACHE_DIR / f"{key}.json", "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# ── Core fetch ────────────────────────────────────────────────────────────────

def _fetch(url: str, timeout: int = 8) -> Optional[str]:
    """Raw HTTP fetch with proper headers to avoid bot blocks."""
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return None


def _html_to_text(html: str, max_chars: int = 3000) -> str:
    """Strip HTML tags and extract readable text."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        # Remove junk tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        return text[:max_chars]
    except ImportError:
        # Fallback: basic regex strip
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text)
        return text[:max_chars]


# ── DuckDuckGo Search ────────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo Lite (no API key needed).
    Returns list of {title, url, snippet}.
    """
    global _last_search_time

    cache_key = _cache_key(f"search:{query}")
    cached = _cache_get(cache_key, max_age_minutes=20)
    if cached:
        return cached

    with _lock:
        # Rate limit
        elapsed = time.time() - _last_search_time
        if elapsed < SEARCH_COOLDOWN:
            time.sleep(SEARCH_COOLDOWN - elapsed)
        _last_search_time = time.time()

    url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
    html = _fetch(url)
    if not html:
        return []

    results = []
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", class_="result-link")
        snippets = soup.find_all("td", class_="result-snippet")

        for i, (link, snip) in enumerate(zip(links, snippets)):
            if i >= max_results:
                break
            results.append({
                "title": link.get_text(strip=True),
                "url": link.get("href", ""),
                "snippet": snip.get_text(strip=True)
            })
    except ImportError:
        # No beautifulsoup — basic regex
        title_pattern = re.compile(r'class="result-link"[^>]*>([^<]+)</a>', re.DOTALL)
        href_pattern = re.compile(r'class="result-link"\s+href="([^"]+)"')
        snip_pattern = re.compile(r'class="result-snippet"[^>]*>([^<]+)</td>', re.DOTALL)

        titles = title_pattern.findall(html)[:max_results]
        hrefs = href_pattern.findall(html)[:max_results]
        snips = snip_pattern.findall(html)[:max_results]

        for t, h, s in zip(titles, hrefs, snips):
            results.append({"title": t.strip(), "url": h.strip(), "snippet": s.strip()})

    _cache_set(cache_key, results)
    return results


def read_page(url: str, max_chars: int = 2000) -> str:
    """Fetch a URL and return its readable text content."""
    cache_key = _cache_key(f"page:{url}")
    cached = _cache_get(cache_key, max_age_minutes=60)
    if cached:
        return cached

    html = _fetch(url)
    if not html:
        return f"Could not fetch {url}"

    text = _html_to_text(html, max_chars=max_chars)
    _cache_set(cache_key, text)
    return text


# ── News ─────────────────────────────────────────────────────────────────────

NEWS_FEEDS = {
    "tech": "https://feeds.feedburner.com/TechCrunch",
    "ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "finance": "https://feeds.finance.yahoo.com/rss/2.0/headline",
    "india": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "crypto": "https://cointelegraph.com/rss",
    "science": "https://www.sciencedaily.com/rss/top.xml",
}


def get_news(topic: str = "tech", max_items: int = 5) -> List[Dict[str, str]]:
    """Fetch news headlines for a topic via RSS."""
    cache_key = _cache_key(f"news:{topic}")
    cached = _cache_get(cache_key, max_age_minutes=30)
    if cached:
        return cached

    feed_url = NEWS_FEEDS.get(topic.lower())
    if not feed_url:
        # Try searching for topic-specific news
        return search_news(topic, max_items)

    try:
        import feedparser
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "published": entry.get("published", "")
            })
        _cache_set(cache_key, items)
        return items
    except ImportError:
        # Fallback to search
        return search_news(topic, max_items)


def search_news(query: str, max_items: int = 5) -> List[Dict[str, str]]:
    """Search for news about a specific topic."""
    results = web_search(f"{query} news today", max_results=max_items)
    return results


# ── Research ─────────────────────────────────────────────────────────────────

def research_topic(query: str, depth: int = 2) -> Dict[str, Any]:
    """
    Multi-step research: search → read top results → synthesize.
    Returns: {query, summary, sources, raw_content}
    """
    cache_key = _cache_key(f"research:{query}")
    cached = _cache_get(cache_key, max_age_minutes=120)
    if cached:
        return cached

    # Step 1: Search
    results = web_search(query, max_results=depth + 2)
    if not results:
        return {"query": query, "summary": "No results found.", "sources": [], "raw_content": ""}

    # Step 2: Read top N pages
    raw_parts = []
    sources = []
    for r in results[:depth]:
        if r.get("url"):
            content = read_page(r["url"], max_chars=1500)
            if content and len(content) > 100:
                raw_parts.append(f"[{r['title']}]\n{content}")
                sources.append({"title": r["title"], "url": r["url"]})

    raw_content = "\n\n---\n\n".join(raw_parts)

    result = {
        "query": query,
        "raw_content": raw_content,
        "sources": sources,
        "search_results": results,
        "fetched_at": datetime.now().isoformat()
    }

    _cache_set(cache_key, result)
    return result


# ── Decision: Should LOVE search? ────────────────────────────────────────────

SEARCH_TRIGGERS = [
    r"\bwhat is\b", r"\bwho is\b", r"\blatest\b", r"\bcurrent\b", r"\bnews\b",
    r"\bprice of\b", r"\bstock\b", r"\bweather\b", r"\btoday\b", r"\brecent\b",
    r"\bhow to\b", r"\bexplain\b", r"\blook up\b", r"\bsearch\b", r"\bfind\b",
    r"\bcheck\b", r"\bwhat happened\b", r"\btell me about\b", r"\bresearch\b",
    r"\blearn about\b", r"\btrend\b", r"\bmarket\b", r"\brelease\b",
]


def should_search(user_input: str) -> bool:
    """Decide if this query needs internet access."""
    text = user_input.lower()
    return any(re.search(p, text) for p in SEARCH_TRIGGERS)


def auto_search_for_query(user_input: str) -> str:
    """
    If the query needs internet, search and return context string
    to inject into the LOVE prompt. Otherwise returns empty string.
    """
    if not should_search(user_input):
        return ""

    try:
        results = web_search(user_input, max_results=3)
        if not results:
            return ""

        lines = [f"WEB SEARCH RESULTS for: '{user_input}'"]
        for r in results:
            lines.append(f"- {r['title']}: {r.get('snippet', '')[:200]}")
            if r.get("url"):
                lines.append(f"  Source: {r['url']}")

        return "\n".join(lines)
    except Exception:
        return ""


# ── Convenience for idle mind ─────────────────────────────────────────────────

def fetch_trending_topics() -> List[str]:
    """Get what's trending right now — for idle exploration."""
    results = web_search("trending today technology AI 2025", max_results=5)
    return [r.get("title", "") for r in results if r.get("title")]


def explore_improvement_ideas() -> List[str]:
    """Search for ideas on how personal AI assistants can improve."""
    results = web_search(
        "personal AI assistant features 2025 improvements autonomous agents",
        max_results=5
    )
    ideas = [r.get("snippet", r.get("title", "")) for r in results]
    return [i for i in ideas if len(i) > 20]
