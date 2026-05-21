# Supabase pgvector backend.

from __future__ import annotations

from typing import Any

from supabase import create_client

from src.chunking import TextChunk
from src.config import Settings, get_settings


def get_supabase(settings: Settings | None = None):
    settings = settings or get_settings()
    if not settings.supabase_configured:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
    return create_client(settings.supabase_url, settings.supabase_service_key)


def upsert_chunks(
    chunks: list[TextChunk],
    embeddings: list[list[float]],
    settings: Settings | None = None,
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings length mismatch")

    client = get_supabase(settings)
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append(
            {
                "url": chunk.url,
                "title": chunk.title,
                "section": chunk.section,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "embedding": emb,
                "metadata": {"source": "fastapi-docs"},
            }
        )

    total = 0
    for i in range(0, len(rows), 50):
        batch = rows[i : i + 50]
        client.table("doc_chunks").upsert(batch, on_conflict="url,chunk_index").execute()
        total += len(batch)
    return total


def search_similar(
    query_embedding: list[float],
    top_k: int | None = None,
    threshold: float = 0.0,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    k = top_k or settings.top_k
    client = get_supabase(settings)
    resp = client.rpc(
        "match_doc_chunks",
        {"query_embedding": query_embedding, "match_count": k, "match_threshold": threshold},
    ).execute()
    return resp.data or []


def chunk_count(settings: Settings | None = None) -> int:
    client = get_supabase(settings)
    resp = client.table("doc_chunks").select("id", count="exact").limit(1).execute()
    return resp.count or 0


def clear_all(settings: Settings | None = None) -> None:
    client = get_supabase(settings)
    client.table("doc_chunks").delete().neq("id", 0).execute()
