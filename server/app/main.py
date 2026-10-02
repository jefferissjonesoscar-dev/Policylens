"""
Entry point for the PolicyLens backend.

Run from the server/ folder:
    python -m app.main
"""

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings  # importing this checks the API key at startup
from app.error_handlers import register_error_handlers
from app.middleware import BodySizeLimitMiddleware
from app.routes import analyze, health, permissions

# Show INFO and above from our modules (retries, rejected inputs, API errors).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="PolicyLens API")

app.add_middleware(BodySizeLimitMiddleware)
register_error_handlers(app)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(permissions.router)

# In production, serve the built React app (client/dist, made by "npm run build")
# from this same server, so the browser talks to one address and no CORS is needed.
# In development the Vite dev server serves the frontend instead, and this is skipped.
CLIENT_BUILD = Path(__file__).resolve().parents[2] / "client" / "dist"
if CLIENT_BUILD.is_dir():
    # Mounted last so the /api routes above take priority.
    app.mount("/", StaticFiles(directory=CLIENT_BUILD, html=True), name="client")


if __name__ == "__main__":
    # reload=True restarts the server when you edit a file (handy in development).
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.port, reload=True)
