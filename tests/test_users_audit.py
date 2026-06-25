"""User management + audit log (M15 / ADR-0006)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import AuditEvent, Role, User


def _admin(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "boss", "admin-pass-123", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "boss", "password": "admin-pass-123"},
    )


def test_login_is_audited(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "u", "good-pass-123", Role.VIEWER)
    client.post(
        "/api/v1/auth/login", json={"username": "u", "password": "wrong"}
    )
    client.post(
        "/api/v1/auth/login",
        json={"username": "u", "password": "good-pass-123"},
    )
    with Session(db.get_engine()) as s:
        actions = [e.action for e in s.exec(select(AuditEvent)).all()]
        assert "login.fail" in actions
        assert "login.ok" in actions
        # never store the password
        for e in s.exec(select(AuditEvent)).all():
            assert "good-pass-123" not in e.detail


def test_user_crud_and_audit(client: TestClient) -> None:
    _admin(client)
    created = client.post(
        "/api/v1/users",
        json={
            "username": "op2",
            "password": "op2-pass-123",
            "role": "operator",
        },
    )
    assert created.status_code == 201
    assert "password" not in created.json()
    uid = created.json()["id"]

    # disable + role change
    client.patch(f"/api/v1/users/{uid}", json={"active": False})
    client.patch(f"/api/v1/users/{uid}", json={"role": "viewer"})

    users = client.get("/api/v1/users").json()
    op2 = next(u for u in users if u["username"] == "op2")
    assert op2["active"] is False and op2["role"] == "viewer"

    audit = client.get("/api/v1/audit").json()
    actions = [a["action"] for a in audit]
    assert "user.create" in actions
    assert "user.disable" in actions
    assert "user.role" in actions


def test_cannot_delete_self(client: TestClient) -> None:
    _admin(client)
    with Session(db.get_engine()) as s:
        me = s.exec(select(User).where(User.username == "boss")).first()
        assert me is not None
        my_id = me.id
    assert client.delete(f"/api/v1/users/{my_id}").status_code == 400


def test_users_admin_only(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "op-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "op-pass-12345"},
    )
    assert client.get("/api/v1/users").status_code == 403
    assert client.get("/api/v1/audit").status_code == 403


def test_audit_page_renders(client: TestClient) -> None:
    _admin(client)
    page = client.get("/portal/audit")
    assert page.status_code == 200
    assert "audit-view" in page.text
    assert "/portal/manage/users" in page.text
