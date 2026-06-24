"""Auth flow + RBAC."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role, User


def _make_user(username: str, password: str, role: Role) -> None:
    with Session(db.get_engine()) as session:
        auth.create_user(session, username, password, role)


def test_login_me_logout(client: TestClient) -> None:
    _make_user("alice", "s3cret-pass", Role.OPERATOR)

    bad = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "wrong"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "s3cret-pass"},
    )
    assert ok.status_code == 200
    assert ok.json() == {"username": "alice", "role": "operator"}

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_require_role(client: TestClient) -> None:
    # mount a guarded route on the running app
    app: FastAPI = client.app  # type: ignore[assignment]

    @app.get("/api/v1/_admin_only")
    def _admin_only(
        user: User = Depends(auth.require_role(Role.ADMIN)),
    ) -> dict[str, str]:
        return {"ok": user.username}

    _make_user("viewer1", "pw-viewer-1", Role.VIEWER)
    _make_user("admin1", "pw-admin-1", Role.ADMIN)

    assert client.get("/api/v1/_admin_only").status_code == 401  # anon

    client.post(
        "/api/v1/auth/login",
        json={"username": "viewer1", "password": "pw-viewer-1"},
    )
    assert client.get("/api/v1/_admin_only").status_code == 403  # wrong role
    client.post("/api/v1/auth/logout")

    client.post(
        "/api/v1/auth/login",
        json={"username": "admin1", "password": "pw-admin-1"},
    )
    assert client.get("/api/v1/_admin_only").status_code == 200
