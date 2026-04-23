# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Main FastAPI application."""

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from teddy_server.api.routes import router as api_router
from teddy_server.core.doll_registry import DollRegistry
from teddy_server.core.session_manager import SessionManager
from teddy_server.services.websocket_handler import websocket_router

# Global state
_doll_registry = DollRegistry()
_session_manager = SessionManager()
_message_queue: asyncio.Queue[dict] = asyncio.Queue()


app = FastAPI(
    title="Tedd-EH Server",
    description="AI-powered doll orchestration server for the Tedd-EH project.",
    version="0.1.0",
)

# Initialize state directly (works with TestClient and lifespan)
app.state.doll_registry = _doll_registry
app.state.session_manager = _session_manager
app.state.message_queue = _message_queue

# Include API routes
app.include_router(api_router)
app.include_router(websocket_router)

# Static files and templates
_static_dir = Path(__file__).parent / "static"
_templates_dir = Path(__file__).parent / "templates"

if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

templates = Jinja2Templates(directory=str(_templates_dir))


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint redirects to dashboard."""
    return {"message": "Tedd-EH Server API", "docs": "/docs", "dashboard": "/dashboard"}


@app.get("/dashboard")
async def dashboard() -> dict[str, str]:
    """Web dashboard for doll control and monitoring."""
    return {"message": "Dashboard - use /static/index.html"}
