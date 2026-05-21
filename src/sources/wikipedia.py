"""
Fetch readable Wikipedia articles via the free MediaWiki API.

Why Wikipedia (not Cricbuzz)?
- Plain-English articles anyone can understand
- Official API (no brittle HTML scraping)
- Cricbuzz is news/scores JS pages — poor fit for stable RAG ingestion
"""

from __future__ import annotations

import time
from urllib.parse import quote

import httpx

from src.config import Settings, get_settings
from src.scraper import DocPage

API = "https://en.wikipedia.org/w/api.php"

# Beginner-friendly set — cricket-heavy + a few general topics
DEFAULT_TOPICS = [
    "Cricket",
    "History of cricket",
    "Test cricket",
    "One Day International",
    "Twenty20",
    "ICC Cricket World Cup",
    "Indian Premier League",
    "India national cricket team",
    "Australia national cricket team",
    "England cricket team",
    "Bowling (cricket)",
    "Batting (cricket)",
    "Fielding (cricket)",
    "Wicket",
    "Run (cricket)",
    "Over (cricket)",
    "Leg before wicket",
    "Cricket ball",
    "Cricket bat",
    "Sachin Tendulkar",
    "Virat Kohli",
    "MS Dhoni",
    "Don Bradman",
    "Earth",
    "Sun",
    "Moon",
    "Human",
    "Internet",
    "Artificial intelligence",
    "Machine learning",
    "Python (programming language)",
    "World Wide Web",
    "Olympic Games",
    "Football",
    "Tennis",
    "Basketball",
    "Cooking",
    "Photosynthesis",
    "Climate change",
    "Solar System",
    "DNA",
    "Vaccine",
    "Renewable energy",
    "Electric vehicle",
    "Smartphone",
    "Social media",
    "E-commerce",
    "Cloud computing",
    "Database",
    "Algorithm",
]


def _wiki_url(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"


def fetch_articles(settings: Settings | None = None) -> list[DocPage]:
    settings = settings or get_settings()
    topics = settings.wikipedia_topic_list or DEFAULT_TOPICS
    topics = topics[: settings.max_ingest_pages]

    pages: list[DocPage] = []

    with httpx.Client(
        timeout=45.0,
        headers={"User-Agent": "WilliamRAG/0.1 (education demo; contact: local)"},
    ) as client:
        # One article per request — batching breaks when one article is very long (e.g. Cricket)
        for i, topic in enumerate(topics, 1):
            params = {
                "action": "query",
                "titles": topic,
                "prop": "extracts|info",
                "explaintext": "1",
                "exchars": 8000,
                "redirects": "1",
                "inprop": "url",
                "format": "json",
            }
            for attempt in range(4):
                resp = client.get(API, params=params)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                break
            else:
                print(f"  [{i}/{len(topics)}] SKIP (rate limited) {topic}")
                continue
            data = resp.json().get("query", {}).get("pages", {})

            for _pid, page in data.items():
                if page.get("missing"):
                    print(f"  [{i}/{len(topics)}] SKIP (not found) {topic}")
                    continue
                title = page.get("title", "Untitled")
                extract = (page.get("extract") or "").strip()
                if len(extract) < 100:
                    print(f"  [{i}/{len(topics)}] SKIP (too short) {title}")
                    continue
                url = page.get("fullurl") or _wiki_url(title)
                section = "cricket" if "cricket" in title.lower() else "general"
                pages.append(
                    DocPage(url=url, title=title, section=section, content=extract)
                )
                print(f"  [{i}/{len(topics)}] OK  {title} ({len(extract)} chars)")

            time.sleep(0.8)

    return pages
