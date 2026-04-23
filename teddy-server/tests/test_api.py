# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from teddy_server.main import app
from teddy_server.models.doll import DollStatus


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestDollEndpoints:
    def test_list_dolls_empty(self, client: TestClient) -> None:
        response = client.get("/api/dolls")
        assert response.status_code == 200
        assert response.json() == []

    def test_register_doll(self, client: TestClient) -> None:
        response = client.post(
            "/api/dolls",
            json={"id": "teddy-01", "name": "Teddy", "capabilities": {"audio": True, "video": True, "servos": 4}},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "teddy-01"
        assert data["name"] == "Teddy"
        assert data["status"] == "idle"

    def test_register_doll_duplicate(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy 2"})
        assert response.status_code == 409

    def test_get_doll(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.get("/api/dolls/teddy-01")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "teddy-01"

    def test_get_doll_not_found(self, client: TestClient) -> None:
        response = client.get("/api/dolls/nonexistent")
        assert response.status_code == 404

    def test_delete_doll(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.delete("/api/dolls/teddy-01")
        assert response.status_code == 204
        assert client.get("/api/dolls/teddy-01").status_code == 404

    def test_update_doll_status(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.patch(
            "/api/dolls/teddy-01/status",
            json={"status": "speaking"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "speaking"


class TestSessionEndpoints:
    def test_create_session(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.post("/api/sessions", json={"doll_id": "teddy-01"})
        assert response.status_code == 201
        data = response.json()
        assert data["doll_id"] == "teddy-01"
        assert data["is_active"] is True

    def test_get_session(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        created = client.post("/api/sessions", json={"doll_id": "teddy-01"}).json()
        response = client.get(f"/api/sessions/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_list_sessions(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        before = len(client.get("/api/sessions").json())
        client.post("/api/sessions", json={"doll_id": "teddy-01"})
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert len(response.json()) == before + 1

    def test_send_text_message(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.post(
            "/api/dolls/teddy-01/message",
            json={"text": "Hello Teddy!"},
        )
        assert response.status_code == 202

    def test_send_servo_command(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.post(
            "/api/dolls/teddy-01/servo",
            json={"channel": 0, "angle": 45, "speed_ms": 100},
        )
        assert response.status_code == 202

    def test_trigger_expression(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.post(
            "/api/dolls/teddy-01/expression",
            json={"name": "happy"},
        )
        assert response.status_code == 202

    def test_trigger_action(self, client: TestClient) -> None:
        client.post("/api/dolls", json={"id": "teddy-01", "name": "Teddy"})
        response = client.post(
            "/api/dolls/teddy-01/action",
            json={"name": "wave_left"},
        )
        assert response.status_code == 202
