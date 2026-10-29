"""Vercel Python function entry point.

vercel.json rewrites every /api/* request here; FastAPI then routes on the
original path, so the same app serves local, Docker and Vercel deployments.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401
