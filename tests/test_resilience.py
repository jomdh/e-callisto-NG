"""Failure-mode matrix + alert channels + notify dedup (M16)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services import alerts
from ecallisto_ng.services.failure_modes import (
    Fault,
    Response,
    policy_for,
    should_pause,
)


def test_failure_matrix_responses() -> None:
    assert policy_for(Fault.DISK_FULL).response is Response.PAUSE
    assert policy_for(Fault.DISK_LOW).response is Response.CONTINUE
    assert policy_for(Fault.RECEIVER_GONE).response is Response.RETRY
    # web down never stops acquisition (independence)
    assert policy_for(Fault.WEB_DOWN).response is Response.CONTINUE
    assert all(policy_for(f).alert for f in Fault)


def test_should_pause() -> None:
    assert should_pause({Fault.DISK_LOW, Fault.UPLOAD_BACKLOG}) is False
    assert should_pause({Fault.DISK_LOW, Fault.DISK_FULL}) is True


class _FakeChannel:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, subject: str, body: str) -> None:
        self.messages.append((subject, body))


class _BrokenChannel:
    def send(self, subject: str, body: str) -> None:
        raise RuntimeError("boom")


def test_dispatch_is_best_effort() -> None:
    good = _FakeChannel()
    assert isinstance(good, alerts.AlertChannel)
    sent = alerts.dispatch([good, _BrokenChannel(), good], "s", "b")
    assert sent == 2  # broken channel didn't block the others
    assert len(good.messages) == 2


def _admin(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "boss", "admin-pass-1", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "boss", "password": "admin-pass-1"},
    )


def test_channel_crud_and_test(client: TestClient) -> None:
    _admin(client)
    # an unreachable webhook still "builds"; test reports 0 sent (best-effort)
    created = client.post(
        "/api/v1/alerts/channels",
        json={"name": "wh", "kind": "webhook", "url": "http://127.0.0.1:9/x"},
    )
    assert created.status_code == 201
    cid = created.json()["id"]
    assert len(client.get("/api/v1/alerts/channels").json()) == 1
    res = client.post(f"/api/v1/alerts/channels/{cid}/test")
    assert res.status_code == 200  # dispatch is best-effort
    assert res.json()["sent"] == 0  # connection refused -> not sent


def test_build_channel_email_needs_smtp() -> None:
    from ecallisto_ng.api.models import AlertChannelConfig

    cfg = AlertChannelConfig(
        name="e", kind="email", recipient="a@b.org", enabled=True
    )
    # no smtp_host configured -> not buildable
    assert alerts.build_channel(cfg) is None
