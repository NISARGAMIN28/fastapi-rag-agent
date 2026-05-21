# Vector index stored as data/chunks.json (cosine search in numpy).

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.chunking import TextChunk
from src.config import Settings, get_settings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHUNKS_FILE = DATA_DIR / "chunks.json"


def _load() -> list[dict[str, Any]]:
    if not CHUNKS_FILE.exists():
        return []
    return json.loads(CHUNKS_FILE.read_text())


def _save(rows: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_FILE.write_text(json.dumps(rows, indent=0))


def upsert_chunks(
    chunks: list[TextChunk],
    embeddings: list[list[float]],
    settings: Settings | None = None,
) -> int:
    settings = settings or get_settings()
    rows = _load()
    index = {(r["url"], r["chunk_index"]): i for i, r in enumerate(rows)}

    for chunk, emb in zip(chunks, embeddings):
        row = {
            "url": chunk.url,
            "title": chunk.title,
            "section": chunk.section,
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "token_count": chunk.token_count,
            "embedding": emb,
            "metadata": {"source": settings.docs_source},
        }
        key = (chunk.url, chunk.chunk_index)
        if key in index:
            rows[index[key]] = row
        else:
            rows.append(row)

    _save(rows)
    return len(chunks)


def search_similar(
    query_embedding: list[float],
    top_k: int | None = None,
    threshold: float = 0.0,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    k = top_k or settings.top_k
    rows = _load()
    if not rows:
        return []

    q = np.array(query_embedding, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-9)
    scored: list[tuple[float, dict]] = []

    for r in rows:
        v = np.array(r["embedding"], dtype=np.float32)
        v = v / (np.linalg.norm(v) + 1e-9)
        sim = float(np.dot(q, v))
        if sim > threshold:
            scored.append((sim, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for sim, r in scored[:k]:
        out.append(
            {
                "id": r.get("id"),
                "url": r["url"],
                "title": r["title"],
                "section": r.get("section"),
                "content": r["content"],
                "chunk_index": r["chunk_index"],
                "metadata": r.get("metadata", {}),
                "similarity": sim,
            }
        )
    return out


def chunk_count(settings: Settings | None = None) -> int:
    return len(_load())


def clear_all(settings: Settings | None = None) -> None:
    if CHUNKS_FILE.exists():
        CHUNKS_FILE.unlink()
