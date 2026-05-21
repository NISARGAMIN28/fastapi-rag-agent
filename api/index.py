"""
Vercel serverless entrypoint — exports the FastAPI ASGI app.

All routes (/health, /ask, /search, /docs) are handled by src.api.
"""

import sys
from pathlib import Path

# Ensure project root is on path when Vercel runs from api/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api import app  # noqa: E402 — Vercel looks for `app`
