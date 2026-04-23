# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""WebSocket event schemas."""

from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base class for all WebSocket events."""

    type: str
    timestamp: float = Field(default_factory=lambda: __import__("time").time())


class AudioChunkEvent(BaseEvent):
    """Audio data from doll to server or server to doll."""

    type: str = "audio_chunk"
    format: str = "pcm_s16le_16khz_mono"
    data: bytes


class VideoFrameEvent(BaseEvent):
    """Video frame from doll to server."""

    type: str = "video_frame"
    format: str = "jpeg_720p"
    data: bytes


class SensorDataEvent(BaseEvent):
    """Sensor telemetry from doll."""

    type: str = "sensor_data"
    data: dict[str, Any]


class PingEvent(BaseEvent):
    """Heartbeat ping from doll."""

    type: str = "ping"


class PongEvent(BaseEvent):
    """Heartbeat pong from server."""

    type: str = "pong"


class TextMessageEvent(BaseEvent):
    """Text message from operator to doll."""

    type: str = "text_message"
    doll_id: str
    text: str


class ServoCommandEvent(BaseEvent):
    """Manual servo control from operator."""

    type: str = "servo_command"
    doll_id: str
    channel: int = Field(..., ge=0, le=15)
    angle: float = Field(..., ge=0, le=180)
    speed_ms: int = Field(0, ge=0)


class ExpressionEvent(BaseEvent):
    """Trigger a preset expression."""

    type: str = "expression"
    doll_id: str
    name: str


class ActionEvent(BaseEvent):
    """Trigger a preset action sequence."""

    type: str = "action"
    doll_id: str
    name: str


class DollStatusEvent(BaseEvent):
    """Server-to-client doll status update."""

    type: str = "doll_status"
    doll_id: str
    status: str
    battery: float | None = None
    rssi: int | None = None


class ConversationEvent(BaseEvent):
    """Conversation message for Web UI."""

    type: str = "conversation"
    doll_id: str
    role: str
    text: str


class LogEvent(BaseEvent):
    """System log message for Web UI."""

    type: str = "log"
    level: str
    message: str


class StopSpeakingEvent(BaseEvent):
    """Tell doll to stop current speech."""

    type: str = "stop_speaking"
    doll_id: str
