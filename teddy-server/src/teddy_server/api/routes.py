# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""REST API routes for doll management."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from teddy_server.models.doll import Doll, DollCapabilities, DollStatus
from teddy_server.models.session import Session

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


# Doll endpoints
@router.get("/dolls")
async def list_dolls(request: Request) -> list[Doll]:
    """List all registered dolls."""
    registry = request.app.state.doll_registry
    return registry.list_dolls()


@router.post("/dolls", status_code=201)
async def register_doll(request: Request, doll_data: dict[str, Any]) -> Doll:
    """Register a new doll."""
    registry = request.app.state.doll_registry
    doll_id = doll_data.get("id")
    name = doll_data.get("name")
    if not doll_id or not name:
        raise HTTPException(status_code=400, detail="id and name are required")

    caps_data = doll_data.get("capabilities", {})
    capabilities = DollCapabilities(**caps_data) if caps_data else DollCapabilities()

    try:
        doll = registry.register_doll(
            id=doll_id,
            name=name,
            capabilities=capabilities,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return doll


@router.get("/dolls/{doll_id}")
async def get_doll(request: Request, doll_id: str) -> Doll:
    """Get a specific doll."""
    registry = request.app.state.doll_registry
    doll = registry.get_doll(doll_id)
    if doll is None:
        raise HTTPException(status_code=404, detail="Doll not found")
    return doll


@router.delete("/dolls/{doll_id}", status_code=204)
async def delete_doll(request: Request, doll_id: str) -> None:
    """Unregister a doll."""
    registry = request.app.state.doll_registry
    registry.unregister_doll(doll_id)


@router.patch("/dolls/{doll_id}/status")
async def update_doll_status(request: Request, doll_id: str, status_data: dict[str, Any]) -> Doll:
    """Update a doll's status."""
    registry = request.app.state.doll_registry
    doll = registry.get_doll(doll_id)
    if doll is None:
        raise HTTPException(status_code=404, detail="Doll not found")

    status_str = status_data.get("status")
    try:
        status = DollStatus(status_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_str}")

    registry.update_doll_status(doll_id, status)
    return registry.get_doll(doll_id)


# Session endpoints
@router.post("/sessions", status_code=201)
async def create_session(request: Request, session_data: dict[str, Any]) -> Session:
    """Create a new conversation session."""
    doll_id = session_data.get("doll_id")
    if not doll_id:
        raise HTTPException(status_code=400, detail="doll_id is required")

    session_manager = request.app.state.session_manager
    return session_manager.create_session(doll_id)


@router.get("/sessions")
async def list_sessions(request: Request) -> list[Session]:
    """List all active sessions."""
    session_manager = request.app.state.session_manager
    return session_manager.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str) -> Session:
    """Get a specific session."""
    session_manager = request.app.state.session_manager
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# Doll control endpoints
@router.post("/dolls/{doll_id}/message", status_code=202)
async def send_text_message(request: Request, doll_id: str, msg_data: dict[str, Any]) -> dict[str, str]:
    """Send a text message to a doll."""
    registry = request.app.state.doll_registry
    if registry.get_doll(doll_id) is None:
        raise HTTPException(status_code=404, detail="Doll not found")

    text = msg_data.get("text", "")
    # Queue message for processing via WebSocket
    await request.app.state.message_queue.put({"doll_id": doll_id, "text": text, "type": "text_message"})
    return {"status": "queued", "doll_id": doll_id}


@router.post("/dolls/{doll_id}/servo", status_code=202)
async def send_servo_command(request: Request, doll_id: str, cmd_data: dict[str, Any]) -> dict[str, str]:
    """Send a servo command to a doll."""
    registry = request.app.state.doll_registry
    if registry.get_doll(doll_id) is None:
        raise HTTPException(status_code=404, detail="Doll not found")

    await request.app.state.message_queue.put({
        "doll_id": doll_id,
        "type": "servo_command",
        **cmd_data,
    })
    return {"status": "queued", "doll_id": doll_id}


@router.post("/dolls/{doll_id}/expression", status_code=202)
async def trigger_expression(request: Request, doll_id: str, expr_data: dict[str, Any]) -> dict[str, str]:
    """Trigger a preset expression on a doll."""
    registry = request.app.state.doll_registry
    if registry.get_doll(doll_id) is None:
        raise HTTPException(status_code=404, detail="Doll not found")

    await request.app.state.message_queue.put({
        "doll_id": doll_id,
        "type": "expression",
        **expr_data,
    })
    return {"status": "queued", "doll_id": doll_id}


@router.post("/dolls/{doll_id}/action", status_code=202)
async def trigger_action(request: Request, doll_id: str, action_data: dict[str, Any]) -> dict[str, str]:
    """Trigger a preset action on a doll."""
    registry = request.app.state.doll_registry
    if registry.get_doll(doll_id) is None:
        raise HTTPException(status_code=404, detail="Doll not found")

    await request.app.state.message_queue.put({
        "doll_id": doll_id,
        "type": "action",
        **action_data,
    })
    return {"status": "queued", "doll_id": doll_id}
