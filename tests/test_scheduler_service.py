"""SchedulerService.tick starts/skips recordings by the window."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, Role, Schedule, Station
from ecallisto_ng.services.recorder import RecorderState, get_recorder
from ecallisto_ng.services.scheduler_service import SchedulerService


def _seed(client: TestClient) -> int:
    """Station (equator) + instrument + sun schedule. Returns iid."""
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "sched-svc-pass", Role.OPERATOR)
        s.add(Station(name="EQ", latitude_deg=0.0, longitude_deg=0.0))
        inst = Instrument(
            name="AUTO", channels=8, sweep_rate_hz=4.0, file_seconds=1
        )
        s.add(inst)
        s.commit()
        s.refresh(inst)
        assert inst.id is not None
        s.add(Schedule(instrument_id=inst.id, kind="sun"))
        s.commit()
        return inst.id


def test_tick_records_inside_window_only(client: TestClient) -> None:
    iid = _seed(client)
    svc = SchedulerService()

    midnight = datetime(2026, 3, 20, 0, tzinfo=UTC)
    with Session(db.get_engine()) as s:
        svc.tick(s, midnight)
    # outside the sun window: nothing started
    assert get_recorder().status(iid).last_file is None

    noon = datetime(2026, 3, 20, 12, tzinfo=UTC)
    with Session(db.get_engine()) as s:
        svc.tick(s, noon)
    assert get_recorder().status(iid).state is RecorderState.RECORDING
    # the window recording is continuous now: stop it (window close)
    get_recorder().stop(iid)
    get_recorder().join(iid, timeout=5.0)


def test_free_run_records_on_desired_and_stops_on_clear(
    client: TestClient,
) -> None:
    from ecallisto_ng.services import recorder_state

    with Session(db.get_engine()) as s:
        inst = Instrument(
            name="FREE", channels=8, sweep_rate_hz=4.0, file_seconds=1
        )
        s.add(inst)
        s.commit()
        s.refresh(inst)
        assert inst.id is not None
        iid = inst.id
    svc = SchedulerService()
    any_time = datetime(2026, 3, 20, 3, tzinfo=UTC)  # no window involved

    recorder_state.set_desired(iid, True)  # operator Record
    with Session(db.get_engine()) as s:
        svc.tick(s, any_time)
    assert get_recorder().status(iid).state is RecorderState.RECORDING

    recorder_state.set_desired(iid, False)  # operator Stop
    with Session(db.get_engine()) as s:
        svc.tick(s, any_time)
    get_recorder().join(iid, timeout=5.0)
    assert get_recorder().status(iid).state is not RecorderState.RECORDING


def test_seed_desired_from_boot(client: TestClient) -> None:
    from ecallisto_ng.services import recorder_state

    with Session(db.get_engine()) as s:
        on = Instrument(name="ON", start_on_boot=True)
        off = Instrument(name="OFF", start_on_boot=False)
        s.add(on)
        s.add(off)
        s.commit()
        s.refresh(on)
        s.refresh(off)
        assert on.id is not None and off.id is not None
        SchedulerService().seed_desired_from_boot(s)
        assert recorder_state.get_desired(s, on.id) is True
        assert recorder_state.get_desired(s, off.id) is False


def test_boot_reconciles_stale_recording_state(client: TestClient) -> None:
    from ecallisto_ng.services import recorder_state

    with Session(db.get_engine()) as s:
        inst = Instrument(name="STALE")
        s.add(inst)
        s.commit()
        s.refresh(inst)
        assert inst.id is not None
        iid = inst.id
    # a killed predecessor left "recording" in the DB
    recorder_state.write(iid, RecorderState.RECORDING, None)
    with Session(db.get_engine()) as s:
        SchedulerService().seed_desired_from_boot(s)
        assert recorder_state.read(s)[iid].state == RecorderState.IDLE
