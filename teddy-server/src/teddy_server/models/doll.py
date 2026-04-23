# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Doll state models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DollStatus(str, Enum):
    """Possible states for a doll."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    OFFLINE = "offline"


class DollCapabilities(BaseModel):
    """Hardware capabilities of a doll."""

    audio: bool = True
    video: bool = True
    servos: int = 0
    leds: bool = False


class Doll(BaseModel):
    """Represents a connected doll."""

    id: str = Field(..., description="Unique doll identifier")
    name: str = Field(..., description="Display name")
    status: DollStatus = DollStatus.OFFLINE
    capabilities: DollCapabilities = Field(default_factory=DollCapabilities)
    battery: float | None = Field(None, ge=0.0, le=100.0)
    wifi_rssi: int | None = Field(None)
    last_seen: float | None = Field(None)
    metadata: dict[str, Any] = Field(default_factory=dict)
