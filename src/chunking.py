# Split pages into overlapping token-sized chunks.

from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken

from src.config import Settings, get_settings
from src.scraper import DocPage

_ENC = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    url: str
    title: str
    section: str
    content: str
    chunk_index: int
    token_count: int


def _count_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def chunk_page(page: DocPage, settings: Settings | None = None) -> list[TextChunk]:
    settings = settings or get_settings()
    size = settings.chunk_size
    overlap = settings.chunk_overlap

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", page.content) if p.strip()]
    chunks: list[TextChunk] = []
    buffer: list[str] = []
    buffer_tokens = 0
    idx = 0

    def flush():
        nonlocal idx, buffer, buffer_tokens
        if not buffer:
            return
        text = "\n\n".join(buffer)
        chunks.append(
            TextChunk(
                url=page.url,
                title=page.title,
                section=page.section,
                content=text,
                chunk_index=idx,
                token_count=_count_tokens(text),
            )
        )
        idx += 1
        if overlap > 0 and buffer:
            tail = text[-overlap * 4 :]
            buffer = [tail] if tail.strip() else []
            buffer_tokens = _count_tokens(tail) if buffer else 0
        else:
            buffer = []
            buffer_tokens = 0

    for para in paragraphs:
        pt = _count_tokens(para)
        if buffer_tokens + pt > size and buffer:
            flush()
        buffer.append(para)
        buffer_tokens += pt
        if buffer_tokens >= size:
            flush()

    if buffer:
        flush()

    return chunks
