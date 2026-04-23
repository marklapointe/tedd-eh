# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from teddy_server.models.doll import Doll, DollStatus, DollCapabilities
from teddy_server.models.session import Session, ConversationMessage
from teddy_server.models.events import (
    AudioChunkEvent,
    VideoFrameEvent,
    SensorDataEvent,
    TextMessageEvent,
    ServoCommandEvent,
    ExpressionEvent,
    ActionEvent,
)


class TestDollModels:
    def test_doll_creation(self) -> None:
        doll = Doll(
            id="teddy-01",
            name="Teddy",
            status=DollStatus.IDLE,
            capabilities=DollCapabilities(audio=True, video=True, servos=4),
        )
        assert doll.id == "teddy-01"
        assert doll.name == "Teddy"
        assert doll.status == DollStatus.IDLE
        assert doll.battery is None

    def test_doll_status_enum(self) -> None:
        assert DollStatus.IDLE.value == "idle"
        assert DollStatus.LISTENING.value == "listening"
        assert DollStatus.THINKING.value == "thinking"
        assert DollStatus.SPEAKING.value == "speaking"
        assert DollStatus.OFFLINE.value == "offline"

    def test_doll_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            Doll(id="teddy-01", name="Teddy", status="invalid")


class TestSessionModels:
    def test_session_creation(self) -> None:
        session = Session(id="sess-01", doll_id="teddy-01")
        assert session.id == "sess-01"
        assert session.doll_id == "teddy-01"
        assert session.messages == []

    def test_conversation_message(self) -> None:
        msg = ConversationMessage(role="user", content="Hello Teddy!")
        assert msg.role == "user"
        assert msg.content == "Hello Teddy!"
        assert msg.image is None

    def test_conversation_message_invalid_role(self) -> None:
        with pytest.raises(ValidationError):
            ConversationMessage(role="invalid", content="Hello")


class TestEventModels:
    def test_audio_chunk_event(self) -> None:
        event = AudioChunkEvent(
            type="audio_chunk",
            timestamp=1713840000.0,
            format="pcm_s16le_16khz_mono",
            data=b"fake_audio_data",
        )
        assert event.type == "audio_chunk"
        assert event.format == "pcm_s16le_16khz_mono"

    def test_video_frame_event(self) -> None:
        event = VideoFrameEvent(
            type="video_frame",
            timestamp=1713840000.0,
            format="jpeg_720p",
            data=b"fake_jpeg_data",
        )
        assert event.type == "video_frame"
        assert event.format == "jpeg_720p"

    def test_sensor_data_event(self) -> None:
        event = SensorDataEvent(
            type="sensor_data",
            timestamp=1713840000.0,
            data={"battery": 3.8, "wifi_rssi": -45},
        )
        assert event.data["battery"] == 3.8
        assert event.data["wifi_rssi"] == -45

    def test_text_message_event(self) -> None:
        event = TextMessageEvent(
            type="text_message",
            doll_id="teddy-01",
            text="Tell me a joke!",
        )
        assert event.doll_id == "teddy-01"
        assert event.text == "Tell me a joke!"

    def test_servo_command_event(self) -> None:
        event = ServoCommandEvent(
            type="servo_command",
            doll_id="teddy-01",
            channel=0,
            angle=45,
            speed_ms=100,
        )
        assert event.channel == 0
        assert event.angle == 45
        assert event.speed_ms == 100

    def test_expression_event(self) -> None:
        event = ExpressionEvent(
            type="expression",
            doll_id="teddy-01",
            name="happy",
        )
        assert event.name == "happy"

    def test_action_event(self) -> None:
        event = ActionEvent(
            type="action",
            doll_id="teddy-01",
            name="wave_left",
        )
        assert event.name == "wave_left"
