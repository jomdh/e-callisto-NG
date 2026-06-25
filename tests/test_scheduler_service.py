"""SchedulerService.tick starts/skips recordings by the window."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, Role, Schedule, Station
from ecallisto_ng.services.recorder import get_recorder
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
    get_recorder().join(iid, timeout=5.0)
    st = get_recorder().status(iid)
    assert st.last_file is not None  # a file was recorded by the schedule
