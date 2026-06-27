# SPDX-License-Identifier: AGPL-3.0-or-later
"""First-class liveness (ADR-0012): the frame heartbeat, STALLED derivation,
and its surfacing on the cockpit, diagnostics, and the live WebSocket."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, RecorderRuntime, Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import diagnostics, liveness, recorder_state
from ecallisto_ng.services.operations import instrument_cockpit

_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=UTC)


def _rt(**kw: object) -> RecorderRuntime:
    base: dict[str, object] = {"instrument_id": 1, "state": "recording"}
    base.update(kw)
    return RecorderRuntime(**base)


# --- the STALLED derivation (pure) ---------------------------------------


def test_fresh_heartbeat_is_not_stalled() -> None:
    row = _rt(last_frame_at=_NOW - timedelta(seconds=10))
    assert liveness.is_stalled(row, 4.0, _NOW) is False
    assert liveness.effective_state(row, 4.0, _NOW) == "recording"


def test_stale_heartbeat_is_stalled() -> None:
    row = _rt(last_frame_at=_NOW - timedelta(seconds=300))
    assert liveness.is_stalled(row, 4.0, _NOW) is True
    assert liveness.effective_state(row, 4.0, _NOW) == liveness.STALLED


def test_idle_is_never_stalled() -> None:
    row = _rt(state="idle", last_frame_at=_NOW - timedelta(seconds=300))
    assert liveness.is_stalled(row, 4.0, _NOW) is False


def test_just_started_without_heartbeat_is_not_stalled() -> None:
    # no frame yet, but only just went RECORDING -> give it grace
    row = _rt(last_frame_at=None, updated_at=_NOW - timedelta(seconds=5))
    assert liveness.is_stalled(row, 4.0, _NOW) is False


def test_mute_from_the_start_is_stalled() -> None:
    # recording claimed for well past the bound with zero frames ever
    row = _rt(last_frame_at=None, updated_at=_NOW - timedelta(seconds=600))
    assert liveness.is_stalled(row, 4.0, _NOW) is True


def test_stall_bound_respects_grace_floor() -> None:
    # fast cadence still never trips before the configured grace
    get_settings.cache_clear()
    assert (
        liveness.stall_bound_seconds(100.0)
        >= get_settings().stall_grace_seconds
    )


# --- the heartbeat write -------------------------------------------------


def test_touch_frame_stamps_last_frame_at(client: TestClient) -> None:
    recorder_state.write(5, "recording", None)
    recorder_state.touch_frame(5)
    with Session(db.get_engine()) as s:
        row = s.get(RecorderRuntime, 5)
        assert row is not None and row.last_frame_at is not None


def test_recording_stamps_heartbeat_via_api(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "lv-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "lv-pass-12345"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "HB", "channels": 8}
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=4")
    from ecallisto_ng.services.recorder import get_recorder

    get_recorder().join(iid, timeout=5.0)
    with Session(db.get_engine()) as s:
        row = s.get(RecorderRuntime, iid)
        assert row is not None and row.last_frame_at is not None


# --- surfacing: cockpit + diagnostics ------------------------------------


def _stalled_instrument(client: TestClient) -> int:
    with Session(db.get_engine()) as s:
        inst = Instrument(name="STALL", channels=8, sweep_rate_hz=4.0)
        s.add(inst)
        s.commit()
        s.refresh(inst)
        iid = inst.id
    assert iid is not None
    recorder_state.write(iid, "recording", "STALL_x.fit")
    # backdate the heartbeat well past the bound
    with Session(db.get_engine()) as s:
        row = s.get(RecorderRuntime, iid)
        assert row is not None
        row.last_frame_at = datetime.now(UTC) - timedelta(seconds=600)
        s.add(row)
        s.commit()
    return iid


def test_cockpit_surfaces_stalled(client: TestClient) -> None:
    _stalled_instrument(client)
    with Session(db.get_engine()) as s:
        rows = instrument_cockpit(s, datetime.now(UTC))
        row = next(r for r in rows if r["name"] == "STALL")
        assert row["state"] == liveness.STALLED


def test_diagnostics_flags_stalled_via_heartbeat(client: TestClient) -> None:
    _stalled_instrument(client)
    with Session(db.get_engine()) as s:
        checks = diagnostics._check_recorder_liveness(s)
    stall = [c for c in checks if "STALLED" in c.detail]
    assert stall, [c.detail for c in checks]


# --- surfacing: live WebSocket status ------------------------------------


def test_ws_emits_stalled_status(client: TestClient) -> None:
    # with a tiny grace, a connection that receives no frames is told it has
    # stalled instead of staring at a frozen canvas.
    os.environ["ECALLISTO_STALL_GRACE_SECONDS"] = "0.05"
    get_settings.cache_clear()
    try:
        with client.websocket_connect("/ws/live/4321") as ws:
            seen = set()
            for _ in range(40):
                msg = ws.receive_json()
                if msg.get("type") == "status":
                    seen.add(msg.get("state"))
                if "stalled" in seen:
                    break
            assert "stalled" in seen
    finally:
        del os.environ["ECALLISTO_STALL_GRACE_SECONDS"]
        get_settings.cache_clear()
