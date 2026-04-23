# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""WebSocket handlers for doll and operator connections."""

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from teddy_server.models.doll import DollStatus
from teddy_server.models.events import (
    AudioChunkEvent,
    ConversationEvent,
    DollStatusEvent,
    LogEvent,
    PongEvent,
    SensorDataEvent,
    VideoFrameEvent,
)

websocket_router = APIRouter()

# Connection managers
_doll_connections: Dict[str, WebSocket] = {}
_operator_connections: Set[WebSocket] = set()


async def _broadcast_to_operators(message: dict) -> None:
    """Broadcast a message to all connected operators."""
    disconnected = set()
    for ws in _operator_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        _operator_connections.discard(ws)


@websocket_router.websocket("/ws/doll/{doll_id}")
async def doll_websocket(websocket: WebSocket, doll_id: str) -> None:
    """WebSocket endpoint for doll clients."""
    await websocket.accept()
    _doll_connections[doll_id] = websocket

    # Update registry
    registry = websocket.app.state.doll_registry
    if registry.get_doll(doll_id) is None:
        registry.register_doll(id=doll_id, name=doll_id)
    registry.update_doll_status(doll_id, DollStatus.IDLE)

    # Notify operators
    await _broadcast_to_operators({
        "type": "doll_connected",
        "doll_id": doll_id,
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "audio_chunk":
                # Forward audio to operators for monitoring
                await _broadcast_to_operators({
                    "type": "audio_chunk",
                    "doll_id": doll_id,
                    "format": data.get("format", "pcm_s16le_16khz_mono"),
                })

            elif msg_type == "video_frame":
                # Forward video to operators
                await _broadcast_to_operators({
                    "type": "video_frame",
                    "doll_id": doll_id,
                    "format": data.get("format", "jpeg_720p"),
                    "data": data.get("data", ""),
                })

            elif msg_type == "sensor_data":
                telemetry = data.get("data", {})
                registry.update_doll_telemetry(
                    doll_id,
                    battery=telemetry.get("battery"),
                    wifi_rssi=telemetry.get("wifi_rssi"),
                )
                await _broadcast_to_operators({
                    "type": "sensor_data",
                    "doll_id": doll_id,
                    "data": telemetry,
                })

            elif msg_type == "conversation":
                await _broadcast_to_operators({
                    "type": "conversation",
                    "doll_id": doll_id,
                    "role": data.get("role", "assistant"),
                    "text": data.get("text", ""),
                })

    except WebSocketDisconnect:
        pass
    finally:
        _doll_connections.pop(doll_id, None)
        registry.update_doll_status(doll_id, DollStatus.OFFLINE)
        await _broadcast_to_operators({
            "type": "doll_disconnected",
            "doll_id": doll_id,
        })


@websocket_router.websocket("/ws/operator")
async def operator_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for operator dashboard clients."""
    await websocket.accept()
    _operator_connections.add(websocket)

    # Send current doll list
    registry = websocket.app.state.doll_registry
    dolls = registry.list_dolls()
    await websocket.send_json({
        "type": "doll_list",
        "dolls": [d.model_dump() for d in dolls],
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            target_doll_id = data.get("doll_id")

            if msg_type == "text_message" and target_doll_id:
                doll_ws = _doll_connections.get(target_doll_id)
                if doll_ws:
                    await doll_ws.send_json({
                        "type": "text_message",
                        "text": data.get("text", ""),
                    })

            elif msg_type == "servo_command" and target_doll_id:
                doll_ws = _doll_connections.get(target_doll_id)
                if doll_ws:
                    await doll_ws.send_json({
                        "type": "servo_command",
                        "channel": data.get("channel", 0),
                        "angle": data.get("angle", 90),
                        "speed_ms": data.get("speed_ms", 0),
                    })

            elif msg_type == "expression" and target_doll_id:
                doll_ws = _doll_connections.get(target_doll_id)
                if doll_ws:
                    await doll_ws.send_json({
                        "type": "expression",
                        "name": data.get("name", "neutral"),
                    })

            elif msg_type == "action" and target_doll_id:
                doll_ws = _doll_connections.get(target_doll_id)
                if doll_ws:
                    await doll_ws.send_json({
                        "type": "action",
                        "name": data.get("name", ""),
                    })

            elif msg_type == "stop_speaking" and target_doll_id:
                doll_ws = _doll_connections.get(target_doll_id)
                if doll_ws:
                    await doll_ws.send_json({"type": "stop_speaking"})

    except WebSocketDisconnect:
        pass
    finally:
        _operator_connections.discard(websocket)
