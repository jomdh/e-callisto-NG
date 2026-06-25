# SPDX-License-Identifier: AGPL-3.0-or-later
"""Device scan wired into the Add Instrument form + wizard (S059)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, Role


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "wire-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "wire-pass-123"},
    )


def test_console_offers_scan_for_instruments(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/manage/instruments")
    assert page.status_code == 200
    js = client.get("/static/js/console.js").text
    # the instruments resource opts into the scan panel, hitting discovery
    assert "scan: true" in js
    assert "/api/v1/discovery/scan" in js
    assert "use selected" in js


def test_wizard_instrument_step_has_scan_and_address(
    client: TestClient,
) -> None:
    # walk to the instrument step (admin -> station -> coords -> instrument)
    client.post(
        "/wizard",
        data={"admin_username": "boss", "admin_password": "very-strong-pw"},
    )
    client.post("/wizard", data={"station_name": "S", "observatory": "O"})
    client.post(
        "/wizard",
        data={"latitude_deg": "47", "longitude_deg": "8", "altitude_m": "5"},
    )
    page = client.get("/wizard")
    assert "Step 4 of 5" in page.text  # instrument step
    assert 'id="scan-btn"' in page.text
    assert 'id="scan-pick"' in page.text
    assert 'name="address"' in page.text  # device address is selectable
    assert "/static/js/device_scan.js" in page.text


def test_wizard_persists_instrument_address(client: TestClient) -> None:
    client.post(
        "/wizard",
        data={"admin_username": "boss", "admin_password": "very-strong-pw"},
    )
    client.post("/wizard", data={"station_name": "S", "observatory": "O"})
    client.post(
        "/wizard",
        data={"latitude_deg": "47", "longitude_deg": "8", "altitude_m": "5"},
    )
    client.post(
        "/wizard",
        data={
            "instrument_name": "Callisto-A",
            "instrument_class": "heterodyne",
            "address": "/dev/ttyUSB0",
            "channels": "200",
        },
    )
    client.post("/wizard", data={})  # review -> finish
    with Session(db.get_engine()) as s:
        inst = s.exec(
            select(Instrument).where(Instrument.name == "Callisto-A")
        ).first()
        assert inst is not None
        assert inst.address == "/dev/ttyUSB0"  # the specific device address


def test_device_scan_asset_served(client: TestClient) -> None:
    r = client.get("/static/js/device_scan.js")
    assert r.status_code == 200
    assert "discovery/scan" in r.text
