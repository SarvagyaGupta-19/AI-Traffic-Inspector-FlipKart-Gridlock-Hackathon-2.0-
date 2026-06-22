"""
Flipkart Gridlock — FastAPI Application
Main application factory with CORS, route registration, and static file serving.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CORS_ORIGINS, EVIDENCE_DIR, UPLOADS_DIR
from app.database import init_db
from app.routes import router as api_router
from app.websocket import websocket_stream
from logic.zone_manager import init_zones

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler — runs setup on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("  FLIPKART GRIDLOCK - Traffic Violation Detection")
    logger.info("=" * 60)
    init_db()
    init_zones()
    logger.info("Backend ready. Docs: http://localhost:8000/docs")
    logger.info("=" * 60)
    yield
    # Shutdown cleanup (if needed in the future)
    logger.info("Shutting down Flipkart Gridlock...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Flipkart Gridlock",
        description="Automated Traffic Violation Detection System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ─── CORS ────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Routes ──────────────────────────────────────────────
    app.include_router(api_router)

    # ─── WebSocket ───────────────────────────────────────────
    @app.websocket("/ws/stream")
    async def ws_endpoint(websocket: WebSocket):
        await websocket_stream(websocket)

    # ─── Static Files ────────────────────────────────────────
    # Serve evidence and upload images
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    app.mount("/evidence", StaticFiles(directory=str(EVIDENCE_DIR)), name="evidence")
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

    # ─── Root ────────────────────────────────────────────────
    @app.get("/")
    async def root():
        return {
            "service": "Flipkart Gridlock",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "api": "/api",
            "websocket": "/ws/stream",
        }

    return app


# Create the app instance
app = create_app()
