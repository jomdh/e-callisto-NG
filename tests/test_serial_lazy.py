# SPDX-License-Identifier: AGPL-3.0-or-later
"""SerialConnection opens lazily; building a driver never touches hardware."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ecallisto_ng.connections.serial_link import SerialConnection
from ecallisto_ng.core.units import InstrumentClass
from ecallisto_ng.services.recorder import build_driver


def test_serial_connection_does_not_open_on_construction() -> None:
    # a bogus port would fail immediately if __init__ opened it
    conn = SerialConnection("/dev/does-not-exist-xyz")
    conn.close()  # no-op before any I/O -- nothing was opened


def test_build_heterodyne_driver_no_hardware() -> None:
    # building + reading capabilities must not open the serial port (this is
    # what the instrument detail page / capabilities endpoint do)
    driver = build_driver("heterodyne", "/dev/does-not-exist-xyz", 1, 200)
    caps = driver.capabilities  # static -> no hardware access
    assert caps.instrument_class is InstrumentClass.HETERODYNE
    from ecallisto_ng.core.contracts import BenchCapable

    assert isinstance(driver, BenchCapable)  # the page's gate, hardware-free


def _login_op(client: TestClient) -> None:
    from sqlmodel import Session

    from ecallisto_ng.api import auth, db
    from ecallisto_ng.api.models import Role

    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "lazy-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "lazy-pass-123"},
    )


def test_overview_serial_failure_is_clean_503(client: TestClient) -> None:
    # a heterodyne instrument on a non-existent port -> clean 503, not a 500
    _login_op(client)
    iid = client.post(
        "/api/v1/instruments",
        json={
            "name": "BADPORT",
            "instrument_class": "heterodyne",
            "address": "/dev/does-not-exist-xyz",
        },
    ).json()["id"]
    r = client.post(f"/api/v1/instruments/{iid}/overview")
    assert r.status_code == 503
    assert "hardware error" in r.json()["detail"]
