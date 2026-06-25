"""DB-backed recorder run-state for cross-process visibility (M21 / F14)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, RecorderRuntime, Role
from ecallisto_ng.services import recorder_state
from ecallisto_ng.services.operations import instrument_cockpit


def test_write_and_read(client: TestClient) -> None:
    recorder_state.write(7, "recording", None)
    with Session(db.get_engine()) as s:
        rows = recorder_state.read(s)
        assert rows[7].state == "recording"
    # update + last_file
    recorder_state.write(7, "idle", "X_20260625_000000_01.fit")
    with Session(db.get_engine()) as s:
        row = s.get(RecorderRuntime, 7)
        assert row is not None
        assert row.state == "idle"
        assert row.last_file is not None and row.last_file.endswith(".fit")


def test_cockpit_reflects_persisted_state(client: TestClient) -> None:
    """A recording started by 'another process' (DB only) is visible."""
    with Session(db.get_engine()) as s:
        inst = Instrument(name="XPROC", channels=8)
        s.add(inst)
        s.commit()
        s.refresh(inst)
        iid = inst.id
    assert iid is not None
    # simulate the acquire daemon writing state to the DB (no in-memory job)
    recorder_state.write(iid, "recording", "XPROC_20260625_010000_01.fit")
    with Session(db.get_engine()) as s:
        rows = instrument_cockpit(s, datetime(2026, 6, 25, 12, tzinfo=UTC))
        row = next(r for r in rows if r["name"] == "XPROC")
        assert row["state"] == "recording"  # cross-process, from the DB
        assert row["last_file"].endswith(".fit")


def test_record_persists_runtime_via_api(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "rs-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "rs-pass-12345"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "REC", "channels": 8}
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=4")
    from ecallisto_ng.services.recorder import get_recorder

    get_recorder().join(iid, timeout=5.0)
    with Session(db.get_engine()) as s:
        row = s.get(RecorderRuntime, iid)
        assert row is not None
        assert row.state == "idle"  # finished -> persisted idle + last_file
        assert row.last_file is not None
