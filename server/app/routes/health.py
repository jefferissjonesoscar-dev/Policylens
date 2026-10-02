"""
Health check: a quick way to confirm the backend is running.

GET /api/health  ->  {"status": "ok"}
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    # Deliberately simple: no API key or model details, so nothing sensitive leaks.
    return {"status": "ok"}
