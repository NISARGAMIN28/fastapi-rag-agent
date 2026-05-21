#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import get_settings


def main() -> int:
    print("\nSetup check\n")
    errors = 0
    if not (ROOT / ".env").exists():
        print("  missing .env")
        return 1

    s = get_settings()
    print(f"  source: {s.docs_source}, store: {s.vector_store}, llm: {s.llm_provider}")

    try:
        from src.vector_store import chunk_count
        n = chunk_count(s)
        if n > 0:
            print(f"  {n} chunks indexed")
        else:
            print("  0 chunks — run: python -m src.ingest")
            errors += 1
    except Exception as e:
        print(f"  store error: {e}")
        errors += 1

    if s.embedding_provider == "local":
        try:
            import fastembed  # noqa: F401
        except ImportError:
            print("  pip install fastembed")
            errors += 1

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
