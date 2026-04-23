# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Tests for doll registry."""

import pytest

from teddy_server.core.doll_registry import DollRegistry
from teddy_server.models.doll import Doll, DollStatus


class TestDollRegistry:
    @pytest.fixture
    def registry(self) -> DollRegistry:
        return DollRegistry()

    def test_register_doll(self, registry: DollRegistry) -> None:
        doll = registry.register_doll(id="teddy-01", name="Teddy")
        assert doll.id == "teddy-01"
        assert doll.name == "Teddy"
        assert doll.status == DollStatus.IDLE

    def test_register_duplicate_raises(self, registry: DollRegistry) -> None:
        registry.register_doll(id="teddy-01", name="Teddy")
        with pytest.raises(ValueError):
            registry.register_doll(id="teddy-01", name="Teddy 2")

    def test_get_doll(self, registry: DollRegistry) -> None:
        registry.register_doll(id="teddy-01", name="Teddy")
        doll = registry.get_doll("teddy-01")
        assert doll is not None
        assert doll.name == "Teddy"

    def test_get_doll_not_found(self, registry: DollRegistry) -> None:
        assert registry.get_doll("nonexistent") is None

    def test_update_doll_status(self, registry: DollRegistry) -> None:
        registry.register_doll(id="teddy-01", name="Teddy")
        registry.update_doll_status("teddy-01", DollStatus.SPEAKING)
        doll = registry.get_doll("teddy-01")
        assert doll is not None
        assert doll.status == DollStatus.SPEAKING

    def test_list_dolls(self, registry: DollRegistry) -> None:
        registry.register_doll(id="teddy-01", name="Teddy")
        registry.register_doll(id="teddy-02", name="Teddy 2")
        dolls = registry.list_dolls()
        assert len(dolls) == 2

    def test_unregister_doll(self, registry: DollRegistry) -> None:
        registry.register_doll(id="teddy-01", name="Teddy")
        registry.unregister_doll("teddy-01")
        assert registry.get_doll("teddy-01") is None

    def test_update_doll_telemetry(self, registry: DollRegistry) -> None:
        registry.register_doll(id="teddy-01", name="Teddy")
        registry.update_doll_telemetry("teddy-01", battery=3.8, wifi_rssi=-45)
        doll = registry.get_doll("teddy-01")
        assert doll is not None
        assert doll.battery == 3.8
        assert doll.wifi_rssi == -45
