# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serial-access preflight check + endpoint (permission check)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services import preflight


def test_serial_access_no_ports_is_graceful() -> None:
    # CI has no serial ports -> 'none', never raises
    result = preflight.serial_access()
    assert result["status"] in {"none", "ok", "denied", "busy", "error"}
    assert "message" in result and "ports" in result


def test_try_open_bad_device() -> None:
    ok, detail = preflight._try_open("/dev/does-not-exist-xyz")
    assert ok is False
    assert isinstance(detail, str)


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "v", "pf-pass-1234", Role.VIEWER)
    client.post(
        "/api/v1/auth/login",
        json={"username": "v", "password": "pf-pass-1234"},
    )


def test_preflight_endpoint(client: TestClient) -> None:
    _login(client)
    body = client.get("/api/v1/system/preflight").json()
    assert "serial" in body
    assert "status" in body["serial"]


def test_system_page_has_preflight(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/system")
    assert page.status_code == 200
    assert 'id="pf-serial"' in page.text
    assert "Check serial access" in page.text
