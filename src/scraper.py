# Load pages from sitemap (FastAPI docs) or Wikipedia API.

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from src.config import Settings, get_settings

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class DocPage:
    url: str
    title: str
    section: str
    content: str


def scrape_all(settings: Settings | None = None) -> list[DocPage]:
    settings = settings or get_settings()
    if settings.docs_source.lower() == "wikipedia":
        from src.sources.wikipedia import fetch_articles

        return fetch_articles(settings)
    return _scrape_html_sitemap(settings)


def _scrape_html_sitemap(settings: Settings) -> list[DocPage]:
    urls = _fetch_sitemap_urls(settings)
    pages: list[DocPage] = []
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for i, url in enumerate(urls, 1):
            page = _scrape_page(url, client)
            if page:
                pages.append(page)
                print(f"[{i}/{len(urls)}] OK  {url}")
            else:
                print(f"[{i}/{len(urls)}] SKIP {url}")
    return pages


def _fetch_sitemap_urls(settings: Settings) -> list[str]:
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(settings.docs_sitemap_url)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

    urls = [loc.text.strip() for loc in root.findall(".//sm:loc", NS) if loc.text]
    base = settings.docs_base_url.rstrip("/")
    filtered = [u for u in urls if u.startswith(base) and not u.endswith((".png", ".jpg", ".pdf"))]
    filtered.sort(key=lambda x: (0 if "/tutorial/" in x else 1, x))
    return filtered[: settings.max_ingest_pages]


def _scrape_page(url: str, client: httpx.Client) -> DocPage | None:
    try:
        resp = client.get(url)
        if resp.status_code != 200:
            return None
        title, content = _extract_main_text(resp.text)
        if len(content) < 200:
            return None
        path = urlparse(url).path.strip("/")
        section = path.split("/")[0] if path else "root"
        return DocPage(url=url, title=title, section=section, content=content)
    except httpx.HTTPError:
        return None


def _extract_main_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.find("title")
    title = title_el.get_text(strip=True) if title_el else "Untitled"
    main = soup.find("article") or soup.find("main") or soup.find("div", class_="md-content")
    if not main:
        main = soup.body or soup
    for tag in main.find_all(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    text = main.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return title, text


def resolve_url(path: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if path.startswith("http"):
        return path
    return urljoin(settings.docs_base_url + "/", path.lstrip("/"))
