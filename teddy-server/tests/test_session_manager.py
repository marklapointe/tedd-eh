# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Tests for session manager."""

import pytest

from teddy_server.core.session_manager import SessionManager
from teddy_server.models.session import ConversationMessage


class TestSessionManager:
    @pytest.fixture
    def manager(self) -> SessionManager:
        return SessionManager()

    def test_create_session(self, manager: SessionManager) -> None:
        session = manager.create_session(doll_id="teddy-01")
        assert session.doll_id == "teddy-01"
        assert session.is_active is True
        assert len(session.messages) == 0

    def test_get_session(self, manager: SessionManager) -> None:
        created = manager.create_session(doll_id="teddy-01")
        retrieved = manager.get_session(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_session_not_found(self, manager: SessionManager) -> None:
        assert manager.get_session("nonexistent") is None

    def test_add_message(self, manager: SessionManager) -> None:
        session = manager.create_session(doll_id="teddy-01")
        msg = ConversationMessage(role="user", content="Hello!")
        manager.add_message(session.id, msg)

        updated = manager.get_session(session.id)
        assert updated is not None
        assert len(updated.messages) == 1
        assert updated.messages[0].content == "Hello!"

    def test_list_sessions(self, manager: SessionManager) -> None:
        s1 = manager.create_session(doll_id="teddy-01")
        s2 = manager.create_session(doll_id="teddy-02")
        sessions = manager.list_sessions()
        assert len(sessions) == 2
        assert {s.id for s in sessions} == {s1.id, s2.id}

    def test_list_sessions_for_doll(self, manager: SessionManager) -> None:
        s1 = manager.create_session(doll_id="teddy-01")
        manager.create_session(doll_id="teddy-02")
        sessions = manager.list_sessions(doll_id="teddy-01")
        assert len(sessions) == 1
        assert sessions[0].id == s1.id

    def test_end_session(self, manager: SessionManager) -> None:
        session = manager.create_session(doll_id="teddy-01")
        manager.end_session(session.id)
        assert manager.get_session(session.id) is None

    def test_get_or_create_session(self, manager: SessionManager) -> None:
        session1 = manager.get_or_create_session(doll_id="teddy-01")
        session2 = manager.get_or_create_session(doll_id="teddy-01")
        assert session1.id == session2.id

    def test_context_window_limit(self, manager: SessionManager) -> None:
        session = manager.create_session(doll_id="teddy-01")
        for i in range(25):
            msg = ConversationMessage(role="user", content=f"Message {i}")
            manager.add_message(session.id, msg)

        updated = manager.get_session(session.id)
        assert updated is not None
        assert len(updated.messages) <= 20
