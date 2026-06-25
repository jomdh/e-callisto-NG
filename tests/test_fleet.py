"""Fleet: token-gated health, peer CRUD, aggregation."""

from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services.fleet import gather_fleet


@dataclass
class _Peer:
    name: str
    base_url: str
    token: str = ""
    enabled: bool = True


def test_gather_fleet_with_stub_fetch() -> None:
    peers = [
        _Peer("a", "http://a"),
        _Peer("b", "http://b"),
        _Peer("c", "http://c", enabled=False),
    ]

    def fetch(url: str, token: str) -> dict | None:
        return {"status": "ok"} if url == "http://a" else None

    rows = gather_fleet(peers, fetch)
    assert len(rows) == 2  # disabled peer skipped
    assert rows[0]["reachable"] is True
    assert rows[1]["reachable"] is False


def _login(client: TestClient, role: Role) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, f"u_{role}", "fleet-pass-1", role)
    client.post(
        "/api/v1/auth/login",
        json={"username": f"u_{role}", "password": "fleet-pass-1"},
    )


def test_fleet_health_token_gate(client: TestClient) -> None:
    # no token configured -> always 403
    assert client.get("/api/v1/fleet/health").status_code == 403

    os.environ["ECALLISTO_FLEET_TOKEN"] = "s3cret"
    get_settings.cache_clear()
    assert client.get("/api/v1/fleet/health?token=wrong").status_code == 403
    ok = client.get("/api/v1/fleet/health?token=s3cret")
    assert ok.status_code == 200
    assert "disk_pct_free" in ok.json()
    del os.environ["ECALLISTO_FLEET_TOKEN"]
    get_settings.cache_clear()


def test_peer_crud_and_aggregate(client: TestClient) -> None:
    _login(client, Role.ADMIN)
    created = client.post(
        "/api/v1/fleet/peers",
        json={"name": "stn2", "base_url": "http://stn2", "token": "t"},
    )
    assert created.status_code == 201
    assert len(client.get("/api/v1/fleet/peers").json()) == 1

    agg = client.get("/api/v1/fleet")
    assert agg.status_code == 200
    body = agg.json()
    assert "self" in body and "peers" in body
    # the unreachable peer is reported, not fatal
    assert body["peers"][0]["reachable"] is False


def test_peer_crud_requires_admin(client: TestClient) -> None:
    _login(client, Role.OPERATOR)
    assert (
        client.post(
            "/api/v1/fleet/peers",
            json={"name": "x", "base_url": "http://x"},
        ).status_code
        == 403
    )
