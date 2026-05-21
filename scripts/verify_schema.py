#!/usr/bin/env python3
"""Check Supabase vector dimension matches config (384 for free local mode)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import get_settings
from src.embeddings import embed_query


def main():
    settings = get_settings()
    emb = embed_query("dimension test")
    dim = len(emb)
    print(f"Local embedding dimension: {dim}")

    from src.vector_store import get_supabase

    client = get_supabase(settings)
    try:
        client.rpc(
            "match_doc_chunks",
            {
                "query_embedding": emb,
                "match_count": 1,
                "match_threshold": 0.0,
            },
        ).execute()
        print("✓ Supabase RPC accepts", dim, "dimensional vectors")
        return 0
    except Exception as e:
        print("✗ Schema mismatch:", e)
        print("\n→ Open Supabase SQL Editor and run: sql/migrate_to_local.sql")
        print("  Then: python -m src.ingest\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
