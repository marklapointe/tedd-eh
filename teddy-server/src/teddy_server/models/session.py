# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Session and conversation models."""

from typing import Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A single message in a conversation."""

    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    image: str | None = None
    emotion_detected: str | None = None
    gesture_detected: list[str] = Field(default_factory=list)
    scene_description: str | None = None


class Session(BaseModel):
    """An active conversation session with a doll."""

    id: str = Field(..., description="Unique session identifier")
    doll_id: str = Field(..., description="ID of the associated doll")
    messages: list[ConversationMessage] = Field(default_factory=list)
    created_at: float = Field(default_factory=lambda: __import__("time").time())
    updated_at: float = Field(default_factory=lambda: __import__("time").time())
    is_active: bool = True
