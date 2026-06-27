# SPDX-License-Identifier: AGPL-3.0-or-later
"""Operations-room IA (ADR-0011, M37): per-instrument workspace shell,
three-group sidebar, and the console's optional per-instrument scoping."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "ws-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "ws-pass-12345"},
    )


def _make(client: TestClient, name: str, klass: str) -> int:
    return client.post(
        "/api/v1/instruments",
        json={"name": name, "instrument_class": klass},
    ).json()["id"]


def test_workspace_shell_has_tabs(client: TestClient) -> None:
    _login(client)
    het = _make(client, "WSHET", "heterodyne")
    page = client.get(f"/portal/instruments/{het}")
    assert page.status_code == 200
    # tabbed shell chrome
    assert 'id="ws-tabs"' in page.text
    assert 'data-tab="overview"' in page.text
    assert 'data-panel="overview"' in page.text
    # all panels render in one page (client-side toggle), so the existing
    # bench-gating asserts still hold; the nonced tab script is present.
    assert 'data-tab="bench"' in page.text  # heterodyne is BenchCapable
    assert "hashchange" in page.text


def test_workspace_bench_tab_gated_by_class(client: TestClient) -> None:
    _login(client)
    sdr = _make(client, "WSSDR", "sdr_soft")
    page = client.get(f"/portal/instruments/{sdr}")
    assert page.status_code == 200
    assert 'data-tab="bench"' not in page.text  # SDR not BenchCapable
    assert "heterodyne (e-Callisto) instruments only" in page.text


def test_sidebar_three_groups(client: TestClient) -> None:
    _login(client)
    text = client.get("/portal").text
    for label in ("Operations Room", "Station", "Admin"):
        assert f">{label}</span>" in text, label
    # instruments still reachable from the room
    assert 'href="/portal/manage/instruments"' in text


def test_console_supports_instrument_scoping(client: TestClient) -> None:
    js = client.get("/static/js/console.js").text
    # the scoping mechanism + a scoped resource are present
    assert "dataset.instrument" in js
    assert "listUrl" in js
    assert 'scope: "instrument_id"' in js  # schedules scope by instrument
