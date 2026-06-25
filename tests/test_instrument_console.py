# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-instrument device console: capabilities + class-gated detail (M25)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "icon-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "icon-pass-123"},
    )


def _make(client: TestClient, name: str, klass: str) -> int:
    return client.post(
        "/api/v1/instruments",
        json={"name": name, "instrument_class": klass},
    ).json()["id"]


def test_capabilities_per_class(client: TestClient) -> None:
    _login(client)
    het = _make(client, "HET", "heterodyne")
    sdr = _make(client, "SDR", "sdr_soft")

    cap_het = client.get(f"/api/v1/instruments/{het}/capabilities").json()
    assert cap_het["instrument_class"] == "heterodyne"
    assert cap_het["bench"] is True  # Callisto is BenchCapable

    cap_sdr = client.get(f"/api/v1/instruments/{sdr}/capabilities").json()
    assert cap_sdr["bench"] is False  # SDR is not BenchCapable


def test_detail_page_gates_bench(client: TestClient) -> None:
    _login(client)
    het = _make(client, "HETD", "heterodyne")
    sdr = _make(client, "SDRD", "sdr_soft")

    het_page = client.get(f"/portal/instruments/{het}")
    assert het_page.status_code == 200
    assert "Detector (bench)" in het_page.text  # bench panel shown
    assert "Noise figure" in het_page.text
    assert "/static/js/instrument.js" in het_page.text
    assert 'data-act="reconnect"' in het_page.text  # heterodyne-only action

    sdr_page = client.get(f"/portal/instruments/{sdr}")
    assert sdr_page.status_code == 200
    assert "Detector (bench)" not in sdr_page.text  # bench hidden for SDR
    assert "heterodyne (e-Callisto) instruments only" in sdr_page.text


def test_detail_404_and_auth(client: TestClient) -> None:
    # anonymous -> redirect to login
    r = client.get("/portal/instruments/1", follow_redirects=False)
    assert r.status_code == 303
    _login(client)
    assert client.get("/portal/instruments/9999").status_code == 404


def test_instruments_list_links_to_detail(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/manage/instruments")
    # the console config exposes an "open" action to the detail page
    assert "/static/js/console.js" in page.text
    js = client.get("/static/js/console.js").text
    assert "/portal/instruments/" in js
