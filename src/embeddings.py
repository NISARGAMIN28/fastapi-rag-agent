# Text embeddings via fastembed (local) or OpenAI.

from __future__ import annotations

from src.config import Settings, get_settings

_local_model = None


def _get_local_model(settings: Settings):
    global _local_model
    if _local_model is None:
        from fastembed import TextEmbedding

        _local_model = TextEmbedding(model_name=settings.embedding_model)
    return _local_model


def embed_texts(texts: list[str], settings: Settings | None = None) -> list[list[float]]:
    settings = settings or get_settings()
    if settings.embedding_provider == "openai":
        return _embed_openai(texts, settings)
    model = _get_local_model(settings)
    return [v.tolist() for v in model.embed(texts)]


def _embed_openai(texts: list[str], settings: Settings) -> list[list[float]]:
    from openai import OpenAI

    if not settings.openai_configured:
        raise RuntimeError("OPENAI_API_KEY required")
    client = OpenAI(api_key=settings.openai_api_key)
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), 64):
        batch = texts[i : i + 64]
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch,
            dimensions=settings.embedding_dimensions,
        )
        ordered = sorted(resp.data, key=lambda d: d.index)
        all_embeddings.extend([d.embedding for d in ordered])
    return all_embeddings


def embed_query(query: str, settings: Settings | None = None) -> list[float]:
    return embed_texts([query], settings)[0]
