#!/usr/bin/env python3
# Scrape docs, chunk, embed, save to vector store.

from __future__ import annotations

import argparse

from src.chunking import chunk_page
from src.config import get_settings
from src.embeddings import embed_texts
from src.scraper import scrape_all
from src.vector_store import chunk_count, clear_all, upsert_chunks


def run(clear: bool = False) -> None:
    settings = get_settings()
    if settings.vector_store == "supabase" and not settings.supabase_configured:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
    if not settings.embeddings_ready:
        raise SystemExit("Embeddings not configured")

    if clear:
        print("Clearing index...")
        clear_all(settings)

    print(f"Loading {settings.docs_source}...")
    pages = scrape_all(settings)
    print(f"Pages: {len(pages)}")

    all_chunks = []
    for page in pages:
        all_chunks.extend(chunk_page(page, settings))
    print(f"Chunks: {len(all_chunks)}")

    embeddings = embed_texts([c.content for c in all_chunks], settings)
    print(f"Saving to {settings.vector_store}...")
    n = upsert_chunks(all_chunks, embeddings, settings)
    print(f"Done. {n} upserted, {chunk_count(settings)} total")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()
    run(clear=args.clear)


if __name__ == "__main__":
    main()
