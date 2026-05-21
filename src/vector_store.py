# Routes to local JSON store or Supabase pgvector.

from __future__ import annotations

from typing import Any

from src.chunking import TextChunk
from src.config import Settings, get_settings


def _backend(settings: Settings):
    if settings.vector_store == "local":
        from src import vector_store_local as store
        return store
    from src import vector_store_supabase as store
    return store


def upsert_chunks(chunks: list[TextChunk], embeddings: list[list[float]], settings: Settings | None = None) -> int:
    return _backend(settings or get_settings()).upsert_chunks(chunks, embeddings, settings)


def search_similar(
    query_embedding: list[float],
    top_k: int | None = None,
    threshold: float = 0.0,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    return _backend(settings or get_settings()).search_similar(
        query_embedding, top_k=top_k, threshold=threshold, settings=settings
    )


def chunk_count(settings: Settings | None = None) -> int:
    return _backend(settings or get_settings()).chunk_count(settings)


def clear_all(settings: Settings | None = None) -> None:
    return _backend(settings or get_settings()).clear_all(settings)
