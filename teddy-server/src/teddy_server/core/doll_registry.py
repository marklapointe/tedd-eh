# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Doll registry for managing connected dolls."""

import time
from typing import Dict, List, Optional

from teddy_server.models.doll import Doll, DollStatus


class DollRegistry:
    """Thread-safe registry of connected dolls."""

    def __init__(self) -> None:
        self._dolls: Dict[str, Doll] = {}

    def register_doll(self, id: str, name: str, **kwargs) -> Doll:
        """Register a new doll. Raises ValueError if ID exists."""
        if id in self._dolls:
            raise ValueError(f"Doll with id '{id}' already registered")

        doll = Doll(
            id=id,
            name=name,
            status=DollStatus.IDLE,
            last_seen=time.time(),
            **kwargs,
        )
        self._dolls[id] = doll
        return doll

    def get_doll(self, doll_id: str) -> Optional[Doll]:
        """Get a doll by ID."""
        return self._dolls.get(doll_id)

    def update_doll_status(self, doll_id: str, status: DollStatus) -> None:
        """Update a doll's status."""
        doll = self._dolls.get(doll_id)
        if doll:
            doll.status = status
            doll.last_seen = time.time()

    def update_doll_telemetry(
        self, doll_id: str, battery: Optional[float] = None, wifi_rssi: Optional[int] = None
    ) -> None:
        """Update a doll's telemetry data."""
        doll = self._dolls.get(doll_id)
        if doll:
            if battery is not None:
                doll.battery = battery
            if wifi_rssi is not None:
                doll.wifi_rssi = wifi_rssi
            doll.last_seen = time.time()

    def list_dolls(self) -> List[Doll]:
        """List all registered dolls."""
        return list(self._dolls.values())

    def unregister_doll(self, doll_id: str) -> None:
        """Remove a doll from the registry."""
        self._dolls.pop(doll_id, None)
