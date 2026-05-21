# HTTP API: /ask, /search, /health, /demo

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from src.config import get_settings
from src.rag import AskResponse, ask, retrieve
from src.vector_store import chunk_count

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"

app = FastAPI(title="Docs RAG Agent", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=20)
    include_generation: bool = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: int | None = Field(default=None, ge=1, le=20)


class HealthResponse(BaseModel):
    status: str
    chunks_indexed: int
    knowledge_base: str
    docs_source: str
    vector_store: str
    embedding_provider: str
    llm_provider: str
    embeddings_ready: bool
    generation_ready: bool


@app.get("/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    try:
        count = chunk_count(settings)
    except Exception:
        count = -1
    return HealthResponse(
        status="ok",
        chunks_indexed=count,
        knowledge_base=settings.knowledge_base_name,
        docs_source=settings.docs_source,
        vector_store=settings.vector_store,
        embedding_provider=settings.embedding_provider,
        llm_provider=settings.llm_provider,
        embeddings_ready=settings.embeddings_ready,
        generation_ready=settings.generation_ready,
    )


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(body: AskRequest):
    settings = get_settings()
    if settings.vector_store == "supabase" and not settings.supabase_configured:
        raise HTTPException(503, "Supabase not configured")
    if not settings.embeddings_ready:
        raise HTTPException(503, "Embeddings not configured")
    if body.include_generation and not settings.generation_ready:
        raise HTTPException(503, f"LLM provider '{settings.llm_provider}' not ready")
    try:
        return ask(body.question, top_k=body.top_k, generate=body.include_generation, settings=settings)
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.post("/search")
def search_endpoint(body: SearchRequest):
    settings = get_settings()
    if not settings.embeddings_ready:
        raise HTTPException(503, "Embeddings not configured")
    try:
        hits = retrieve(body.query, top_k=body.top_k, settings=settings)
        return {"query": body.query, "results": hits}
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.get("/demo")
def demo_ui():
    index = PUBLIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "public/index.html missing")
    return FileResponse(index)


@app.get("/")
def root():
    if (PUBLIC_DIR / "index.html").exists():
        return RedirectResponse("/demo")
    s = get_settings()
    return {"service": f"{s.knowledge_base_name} RAG", "endpoints": ["/demo", "/health", "/ask", "/search"]}
