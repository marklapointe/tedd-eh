# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Session manager for doll conversations."""

import time
import uuid
from typing import Dict, List, Optional

from teddy_server.models.session import ConversationMessage, Session


class SessionManager:
    """Manages active conversation sessions."""

    MAX_CONTEXT_MESSAGES = 20
    SUMMARIZE_THRESHOLD = 10

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create_session(self, doll_id: str) -> Session:
        """Create a new session for a doll."""
        session = Session(
            id=f"sess-{uuid.uuid4().hex[:8]}",
            doll_id=doll_id,
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_or_create_session(self, doll_id: str) -> Session:
        """Get existing active session for doll or create new one."""
        for session in self._sessions.values():
            if session.doll_id == doll_id and session.is_active:
                return session
        return self.create_session(doll_id)

    def add_message(self, session_id: str, message: ConversationMessage) -> None:
        """Add a message to a session, managing context window."""
        session = self._sessions.get(session_id)
        if session is None:
            return

        session.messages.append(message)
        session.updated_at = time.time()

        # Trim context window if needed
        if len(session.messages) > self.MAX_CONTEXT_MESSAGES:
            # Keep system messages and last N messages
            system_msgs = [m for m in session.messages if m.role == "system"]
            other_msgs = [m for m in session.messages if m.role != "system"]
            kept = other_msgs[-(self.MAX_CONTEXT_MESSAGES - len(system_msgs)) :]
            session.messages = system_msgs + kept

    def list_sessions(self, doll_id: Optional[str] = None) -> List[Session]:
        """List all sessions, optionally filtered by doll."""
        sessions = list(self._sessions.values())
        if doll_id:
            sessions = [s for s in sessions if s.doll_id == doll_id]
        return sessions

    def end_session(self, session_id: str) -> None:
        """End and remove a session."""
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False
            del self._sessions[session_id]
