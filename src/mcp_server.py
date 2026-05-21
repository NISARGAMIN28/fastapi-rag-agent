#!/usr/bin/env python3
# MCP server — search and Q&A tools for Cursor / Claude Desktop.

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from src.config import get_settings
from src.rag import ask, format_citations_markdown, retrieve
from src.vector_store import chunk_count

mcp = FastMCP(
    "fastapi-docs-kb",
    instructions=(
        "FastAPI documentation at fastapi.tiangolo.com. "
        "search_docs for retrieval; ask_docs for answers with citations."
    ),
)


@mcp.tool()
def search_docs(query: str, top_k: int = 5) -> str:
    """Semantic search. Returns JSON with url, title, snippet, similarity."""
    settings = get_settings()
    k = max(1, min(top_k, 10))
    hits = retrieve(query, top_k=k, settings=settings)
    slim = [
        {
            "url": h.get("url"),
            "title": h.get("title"),
            "section": h.get("section"),
            "similarity": round(h.get("similarity", 0), 4),
            "snippet": (h.get("content") or "")[:400],
        }
        for h in hits
    ]
    return json.dumps({"query": query, "results": slim}, indent=2)


@mcp.tool()
def ask_docs(question: str, top_k: int = 5) -> str:
    """RAG answer with citations. Returns JSON: answer, citations, sources_markdown."""
    settings = get_settings()
    resp = ask(question, top_k=top_k, generate=True, settings=settings)
    payload = {
        "question": resp.question,
        "answer": resp.answer,
        "citations": [c.model_dump() for c in resp.citations],
        "sources_markdown": format_citations_markdown(resp.citations),
        "retrieved_count": resp.retrieved_count,
    }
    return json.dumps(payload, indent=2)


@mcp.tool()
def format_citations(citations_json: str) -> str:
    """Turn citation JSON into a markdown source list."""
    from src.rag import Citation

    data = json.loads(citations_json)
    if isinstance(data, dict) and "citations" in data:
        items = data["citations"]
    else:
        items = data
    citations = [Citation(**c) for c in items]
    return format_citations_markdown(citations)


@mcp.tool()
def kb_status() -> str:
    """Chunk count and which services are configured."""
    settings = get_settings()
    try:
        count = chunk_count(settings) if settings.supabase_configured else 0
    except Exception as e:
        count = -1
        err = str(e)
    else:
        err = None
    return json.dumps(
        {
            "chunks_indexed": count,
            "supabase": settings.supabase_configured,
            "openai": settings.openai_configured,
            "anthropic": settings.anthropic_configured,
            "error": err,
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
