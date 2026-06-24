"""Health: alert logic (pure) + endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.health import compute_alerts


def test_compute_alerts() -> None:
    assert compute_alerts(50.0, 2, 0, True) == []
    assert "Disk space low (under 10% free)" in compute_alerts(5.0, 1, 0, None)
    assert "No instruments configured" in compute_alerts(50.0, 0, 0, None)
    assert "100 files pending upload" in compute_alerts(50.0, 1, 100, None)
    assert "System clock is not synchronized" in compute_alerts(
        50.0, 1, 0, False
    )
    # unknown clock does not alert
    assert all("clock" not in a for a in compute_alerts(50.0, 1, 0, None))


def test_health_endpoint(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "health-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "health-pass-12"},
    )
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["instruments"] == 0
    assert "No instruments configured" in body["alerts"]
    assert body["disk_total_bytes"] > 0


def test_system_page(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "v", "health-pass-12", Role.VIEWER)
    client.post(
        "/api/v1/auth/login",
        json={"username": "v", "password": "health-pass-12"},
    )
    resp = client.get("/portal/system")
    assert resp.status_code == 200
    assert "System health" in resp.text
