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


def test_workspace_has_data_tab(client: TestClient) -> None:
    _login(client)
    het = _make(client, "WSDATA", "heterodyne")
    page = client.get(f"/portal/instruments/{het}").text
    assert 'data-tab="data"' in page
    assert 'id="ws-data-files"' in page
    assert "loadWorkspaceData" in page  # lazy-loaded on tab open
    assert 'data-iname="WSDATA"' in page  # name-scoped fetch


def test_files_endpoint_accepts_instrument_filter(client: TestClient) -> None:
    _login(client)
    r = client.get("/api/v1/files?instrument=NOPE")
    assert r.status_code == 200
    assert r.json() == []  # no recordings for that instrument


def test_upload_queue_filters_by_instrument(client: TestClient) -> None:
    _login(client)
    # a target to satisfy the FK, then two jobs for two instruments
    from ecallisto_ng.api.models import UploadJob, UploadTarget

    with Session(db.get_engine()) as s:
        t = UploadTarget(name="T", protocol="local", host="/tmp")
        s.add(t)
        s.commit()
        s.refresh(t)
        s.add(UploadJob(target_id=t.id, filename="CALA_20260627.fit.gz"))
        s.add(UploadJob(target_id=t.id, filename="CALB_20260627.fit.gz"))
        s.commit()

    assert len(client.get("/api/v1/upload/queue").json()) == 2
    only_a = client.get("/api/v1/upload/queue?instrument=CALA").json()
    assert len(only_a) == 1
    assert only_a[0]["filename"].startswith("CALA_")


def test_workspace_shows_instrument_id(client: TestClient) -> None:
    # every workspace makes the station instrument id (#N) unmistakable
    _login(client)
    het = _make(client, "IDCALL", "heterodyne")
    page = client.get(f"/portal/instruments/{het}").text
    assert 'class="inst-id">#' + str(het) in page
    # and each config tab names the instrument it applies to
    assert f"#{het} IDCALL" in page


def test_dashboard_tiles_show_instrument_id(client: TestClient) -> None:
    _login(client)
    iid = _make(client, "DASHID", "heterodyne")
    page = client.get("/portal").text
    assert 'class="inst-id">#' + str(iid) in page


def test_console_resolves_instrument_id(client: TestClient) -> None:
    # tables render instrument_id as "#id name"; schedules pick an instrument
    js = client.get("/static/js/console.js").text
    assert "instLabel" in js
    assert "renderCell" in js
    assert "instSelect" in js


def test_console_setups_above_collapsible_form(client: TestClient) -> None:
    # current setups list on top; create form collapsed below behind "+ New"
    js = client.get("/static/js/console.js").text
    assert "console-toolbar" in js
    assert "console-list" in js
    assert "console-form" in js
    assert "setForm" in js  # the collapse toggle
    css = client.get("/static/css/portal.css").text
    assert ".console-list table" in css  # styled, M3-consistent table


def test_programs_list_shows_used_by(client: TestClient) -> None:
    # the shared Programs library shows which instruments use each program
    _login(client)
    pid = client.post(
        "/api/v1/programs",
        json={"name": "P45", "frequencies": [45.0, 46.0]},
    ).json()["id"]
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "PUSER", "program_id": pid},
    ).json()["id"]
    progs = client.get("/api/v1/programs").json()
    prog = next(x for x in progs if x["id"] == pid)
    assert prog["used_by"] == [iid]
    # an unreferenced program reads as empty
    pid2 = client.post(
        "/api/v1/programs",
        json={"name": "PLONE", "frequencies": [50.0]},
    ).json()["id"]
    lone = next(
        x for x in client.get("/api/v1/programs").json() if x["id"] == pid2
    )
    assert lone["used_by"] == []
    js = client.get("/static/js/console.js").text
    assert "used_by" in js  # rendered as #id name / "unused"


def test_calibration_list_shows_used_by(client: TestClient) -> None:
    _login(client)
    cid = client.post(
        "/api/v1/calibration",
        json={"name": "C1", "coefficients": [[10, 40, 1, 2.7]]},
    ).json()["id"]
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "CUSER", "calibration_set_id": cid},
    ).json()["id"]
    sets = client.get("/api/v1/calibration").json()
    cset = next(x for x in sets if x["id"] == cid)
    assert cset["used_by"] == [iid]


def test_dashboard_controls_continuous_and_responsive(
    client: TestClient,
) -> None:
    # the cockpit record button does a continuous record (not a frames=200
    # in-web capture that 409s against the acquire daemon), reports a result,
    # and each card can drill into the workspace.
    js = client.get("/static/js/dashboard.js").text
    assert "frames=200" not in js  # no bounded in-web capture
    assert "/record`" in js  # continuous record (no frames param)
    assert 'data-field="msg"' in js  # writes feedback to the card
    _login(client)
    iid = _make(client, "DASHOP", "heterodyne")
    page = client.get("/portal").text
    assert f'href="/portal/instruments/{iid}">open' in page  # drill-in
    assert 'data-field="msg"' in page  # per-card feedback element


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
