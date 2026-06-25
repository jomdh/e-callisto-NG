"""Remote-access modes: Caddyfile generation, DDNS, settings API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.caddy import build_caddyfile
from ecallisto_ng.services.ddns import build_update_url


def test_caddyfile_modes() -> None:
    lan = build_caddyfile("lan", "", 8000, "")
    assert "tls internal" in lan and "127.0.0.1:8000" in lan

    pub = build_caddyfile("public", "obs.example.org", 8000, "a@b.org")
    assert "obs.example.org {" in pub and "email a@b.org" in pub

    tun = build_caddyfile("tunnel", "relay.example", 8000, "")
    assert "tunnel mode" in tun

    with pytest.raises(ValueError):
        build_caddyfile("public", "", 8000, "")  # needs hostname
    with pytest.raises(ValueError):
        build_caddyfile("bogus", "", 8000, "")


def test_ddns_url() -> None:
    assert (
        build_update_url("https://dyn.example/?myip={ip}", "1.2.3.4")
        == "https://dyn.example/?myip=1.2.3.4"
    )
    with pytest.raises(ValueError):
        build_update_url("https://dyn.example/no-placeholder", "1.2.3.4")


def _login(client: TestClient, role: Role) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, f"u_{role}", "access-pass-1", role)
    client.post(
        "/api/v1/auth/login",
        json={"username": f"u_{role}", "password": "access-pass-1"},
    )


def test_access_settings_and_caddyfile(client: TestClient) -> None:
    _login(client, Role.ADMIN)
    assert client.get("/api/v1/access").json()["mode"] == "lan"  # default

    client.put(
        "/api/v1/access",
        json={
            "mode": "public",
            "hostname": "stn.example.org",
            "tls_email": "op@example.org",
        },
    )
    assert client.get("/api/v1/access").json()["mode"] == "public"

    cf = client.get("/api/v1/access/caddyfile")
    assert cf.status_code == 200
    assert "stn.example.org" in cf.text


def test_access_put_requires_admin(client: TestClient) -> None:
    _login(client, Role.OPERATOR)
    assert (
        client.put("/api/v1/access", json={"mode": "lan"}).status_code == 403
    )
