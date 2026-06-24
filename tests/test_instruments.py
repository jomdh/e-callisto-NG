"""Instrument CRUD + RBAC + record control."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.recorder import RecorderState, get_recorder


def _login(client: TestClient, role: Role) -> None:
    name = f"u_{role}"
    with Session(db.get_engine()) as session:
        auth.create_user(session, name, "password-123", role)
    client.post(
        "/api/v1/auth/login",
        json={"username": name, "password": "password-123"},
    )


def test_crud_and_rbac(client: TestClient) -> None:
    _login(client, Role.VIEWER)
    assert client.get("/api/v1/instruments").json() == []
    # viewer cannot create
    assert (
        client.post("/api/v1/instruments", json={"name": "x"}).status_code
        == 403
    )
    client.post("/api/v1/auth/logout")

    _login(client, Role.OPERATOR)
    created = client.post(
        "/api/v1/instruments",
        json={"name": "CALLISTO-01", "channels": 8},
    )
    assert created.status_code == 201
    iid = created.json()["id"]

    got = client.get(f"/api/v1/instruments/{iid}")
    assert got.json()["name"] == "CALLISTO-01"

    patched = client.patch(
        f"/api/v1/instruments/{iid}",
        json={"name": "CALLISTO-01", "channels": 16},
    )
    assert patched.json()["channels"] == 16

    assert client.delete(f"/api/v1/instruments/{iid}").status_code == 204
    assert client.get(f"/api/v1/instruments/{iid}").status_code == 404


def test_record_to_file(client: TestClient) -> None:
    _login(client, Role.OPERATOR)
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "RECSTN", "channels": 8},
    ).json()["id"]

    started = client.post(f"/api/v1/instruments/{iid}/record?frames=5")
    assert started.status_code == 200
    assert started.json()["state"] == "recording"

    get_recorder().join(iid, timeout=5.0)

    st = client.get(f"/api/v1/instruments/{iid}/status").json()
    assert st["state"] == RecorderState.IDLE
    assert st["last_file"] is not None
    assert Path(st["last_file"]).exists()
