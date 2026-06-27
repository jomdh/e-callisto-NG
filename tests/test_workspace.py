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


def test_workspace_has_live_and_config_tabs(client: TestClient) -> None:
    _login(client)
    het = _make(client, "WSLC", "heterodyne")
    page = client.get(f"/portal/instruments/{het}").text
    # Live tab + its panels (waterfall island), lazy-started on activation
    assert 'data-tab="live"' in page
    assert 'id="waterfall"' in page
    assert "window.startWaterfall" in page
    assert "/static/js/waterfall.js" in page
    # Config tab: a real edit form that PATCHes the instrument
    assert 'data-tab="config"' in page
    assert 'id="ws-config-form"' in page
    assert "PATCH" in page


def test_config_edit_patches_instrument(client: TestClient) -> None:
    _login(client)
    iid = _make(client, "WSCFG", "heterodyne")
    # the form pre-fills current values
    page = client.get(f"/portal/instruments/{iid}").text
    assert 'value="WSCFG"' in page
    # and the PATCH endpoint the form posts to actually updates
    r = client.patch(
        f"/api/v1/instruments/{iid}",
        json={"name": "WSCFG2", "gain": 99, "channels": 8},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "WSCFG2"
    assert r.json()["gain"] == 99


def test_workspace_has_schedule_and_programs_tabs(client: TestClient) -> None:
    _login(client)
    het = _make(client, "WSSP", "heterodyne")
    page = client.get(f"/portal/instruments/{het}").text
    # schedule tab: a console scoped to this instrument
    assert 'data-tab="schedule"' in page
    assert f'data-resource="schedules" data-instrument="{het}"' in page
    # programs tab: the shared library console (unscoped)
    assert 'data-tab="programs"' in page
    assert 'data-resource="programs"' in page
    assert "/static/js/console.js" in page


def test_schedules_list_filters_by_instrument(client: TestClient) -> None:
    _login(client)
    a = _make(client, "SCHA", "heterodyne")
    b = _make(client, "SCHB", "heterodyne")
    client.post(
        "/api/v1/schedules",
        json={"instrument_id": a, "kind": "manual"},
    )
    client.post(
        "/api/v1/schedules",
        json={"instrument_id": b, "kind": "manual"},
    )
    # unscoped -> both
    assert len(client.get("/api/v1/schedules").json()) == 2
    # scoped -> only that instrument's
    only_a = client.get(f"/api/v1/schedules?instrument_id={a}").json()
    assert len(only_a) == 1
    assert only_a[0]["instrument_id"] == a


def test_console_supports_multiple_mounts(client: TestClient) -> None:
    # the workspace mounts a schedules console AND a programs console on one
    # page, so the island must init every [data-resource], not just #console
    js = client.get("/static/js/console.js").text
    assert "querySelectorAll" in js
    assert "mountConsole" in js


def test_workspace_has_calibration_tab(client: TestClient) -> None:
    _login(client)
    het = _make(client, "WSCAL", "heterodyne")
    page = client.get(f"/portal/instruments/{het}").text
    assert 'data-tab="calibration"' in page
    assert 'data-resource="calibration"' in page


def test_workspace_bench_has_att_parity(client: TestClient) -> None:
    # the per-instrument Bench tab keeps the standalone bench's NF Att field
    _login(client)
    het = _make(client, "WSATT", "heterodyne")
    page = client.get(f"/portal/instruments/{het}").text
    assert 'id="d-att"' in page
    js = client.get("/static/js/instrument.js").text
    assert "att_db" in js


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
