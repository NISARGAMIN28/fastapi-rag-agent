# Retrieve chunks, build citations, generate answers.

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from src.config import Settings, get_settings
from src.embeddings import embed_query
from src.llm import generate_answer as llm_generate
from src.vector_store import search_similar


class Citation(BaseModel):
    index: int
    url: str
    title: str
    section: str | None = None
    snippet: str
    similarity: float | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    retrieved_count: int


def _format_context(hits: list[dict[str, Any]]) -> tuple[str, list[Citation]]:
    citations: list[Citation] = []
    blocks: list[str] = []
    for i, hit in enumerate(hits, start=1):
        snippet = (hit.get("content") or "")[:600]
        cit = Citation(
            index=i,
            url=hit.get("url", ""),
            title=hit.get("title") or "Untitled",
            section=hit.get("section"),
            snippet=snippet,
            similarity=hit.get("similarity"),
        )
        citations.append(cit)
        blocks.append(f"[{i}] {cit.title}\nURL: {cit.url}\n---\n{hit.get('content', '')}")
    return "\n\n".join(blocks), citations


def retrieve(question: str, top_k: int | None = None, settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    embedding = embed_query(question, settings)
    return search_similar(embedding, top_k=top_k, settings=settings)


def generate_answer(question: str, hits: list[dict[str, Any]], settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    context, _ = _format_context(hits)
    return llm_generate(question, context, settings)


def ask(
    question: str,
    top_k: int | None = None,
    generate: bool = True,
    settings: Settings | None = None,
) -> AskResponse:
    settings = settings or get_settings()
    hits = retrieve(question, top_k=top_k, settings=settings)
    _, citations = _format_context(hits)

    if generate and hits:
        answer = generate_answer(question, hits, settings)
    elif not hits:
        answer = "No relevant docs found. Try rephrasing or run ingest."
    else:
        answer = _retrieval_only_summary(question, hits)

    return AskResponse(
        question=question,
        answer=answer,
        citations=citations,
        retrieved_count=len(hits),
    )


def _retrieval_only_summary(question: str, hits: list[dict[str, Any]]) -> str:
    lines = [f"Top matches for: {question}"]
    for i, h in enumerate(hits, 1):
        lines.append(f"[{i}] {h.get('title')} — {h.get('url')}")
    return "\n".join(lines)


def format_citations_markdown(citations: list[Citation]) -> str:
    lines = ["### Sources"]
    for c in citations:
        lines.append(f"- [{c.index}] [{c.title}]({c.url})")
    return "\n".join(lines)


def citations_for_eval(
    expected_urls: list[str],
    retrieved: list[dict[str, Any]],
    k: int = 5,
) -> dict[str, Any]:
    top = retrieved[:k]
    retrieved_urls = {h.get("url", "") for h in top}
    expected_set = set(expected_urls)
    if not expected_set:
        return {"precision_at_k": 0.0, "hit": False, "retrieved_urls": list(retrieved_urls)}

    hits = expected_set & retrieved_urls
    precision = len(hits) / min(k, len(top)) if top else 0.0
    return {
        "precision_at_k": precision,
        "hit": bool(hits),
        "matched_urls": list(hits),
        "retrieved_urls": list(retrieved_urls),
    }
