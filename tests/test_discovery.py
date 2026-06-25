# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hardware discovery: serial/USB scan + Callisto probe + endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services import discovery


def test_discovered_device_as_dict_hex() -> None:
    d = discovery.DiscoveredDevice(
        address="/dev/ttyUSB0",
        kind="serial",
        description="PL2303",
        vid=0x067B,
        pid=0x2303,
        suggested_class="heterodyne",
        callisto=True,
        detail="$CRX:Stopped",
    )
    out = d.as_dict()
    assert out["vid"] == "067b" and out["pid"] == "2303"
    assert out["suggested_class"] == "heterodyne"
    assert out["callisto"] is True


def test_probe_callisto_bad_port_is_graceful() -> None:
    ok, info = discovery.probe_callisto("/dev/does-not-exist", timeout=0.1)
    assert ok is False
    assert "open failed" in info or "pyserial" in info


def test_discover_returns_list() -> None:
    # no hardware in CI -> empty/partial, but must not raise
    devices = discovery.discover(probe=False)
    assert isinstance(devices, list)


def test_known_sdr_table_classifies_rx888() -> None:
    # the RX-888 MkII bootloader (Cypress FX3) is a recognized SDR
    assert (0x04B4, 0x00F3) in discovery._KNOWN_SDR
    assert (0x067B, 0x2303) in discovery._SERIAL_BRIDGES  # PL2303 bridge


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "scan-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "scan-pass-123"},
    )


def test_scan_endpoint(client: TestClient) -> None:
    _login(client)
    body = client.get("/api/v1/discovery/scan").json()
    assert body["probed"] is False
    assert "devices" in body and isinstance(body["devices"], list)
    assert "count" in body


def test_scan_open_during_wizard(client: TestClient) -> None:
    # first-run (no users yet) -> the wizard can scan without a login
    body = client.get("/api/v1/discovery/scan").json()
    assert "devices" in body and "count" in body


def test_scan_requires_operator(client: TestClient) -> None:
    # viewer cannot scan (it touches hardware)
    with Session(db.get_engine()) as s:
        auth.create_user(s, "viewer", "view-pass-123", Role.VIEWER)
    client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "view-pass-123"},
    )
    assert client.get("/api/v1/discovery/scan").status_code == 403


def test_hardware_page(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/hardware")
    assert page.status_code == 200
    assert "hw-scan" in page.text
    assert "/static/js/hardware.js" in page.text
