# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tracked-source window engine (M35) + preview honours kind/horizon."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, Role, Schedule, Station
from ecallisto_ng.services.scheduler import source_window, sun_window


def test_sun_delegates_to_sun_window() -> None:
    d = date(2026, 6, 26)
    assert source_window("sun", 40.0, -3.0, d) == sun_window(40.0, -3.0, d)


def test_tracked_source_has_a_window() -> None:
    d = date(2026, 6, 26)
    w = source_window("jupiter", 40.0, -3.0, d)
    assert w is not None and w[1] > w[0]


def test_source_never_up_is_none() -> None:
    # a far-southern source from a far-northern station never rises
    d = date(2026, 6, 26)
    assert source_window("sgr_a", 75.0, 0.0, d) is None


def test_circumpolar_source_records_all_day() -> None:
    # Cas A (dec +58) is circumpolar from 75N -> the whole UT day
    d = date(2026, 6, 26)
    w = source_window("cas_a", 75.0, 0.0, d)
    assert w is not None
    assert (w[1] - w[0]).total_seconds() > 20 * 3600


def _seed(client: TestClient, kind: str, **kw: object) -> int:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "m35-pass-1234", Role.OPERATOR)
        s.add(Station(name="EQ", latitude_deg=0.0, longitude_deg=0.0))
        inst = Instrument(name="I")
        s.add(inst)
        s.commit()
        s.refresh(inst)
        assert inst.id is not None
        sched = Schedule(
            instrument_id=inst.id, kind=kind, **kw  # type: ignore[arg-type]
        )
        s.add(sched)
        s.commit()
        s.refresh(sched)
        assert sched.id is not None
        return sched.id


def test_preview_honours_fixed_kind(client: TestClient) -> None:
    # a fixed schedule must preview via fixed_window, not the sun window
    sid = _seed(client, "fixed", start_utc="08:00", stop_utc="09:00")
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "m35-pass-1234"},
    )
    r = client.get(f"/api/v1/schedules/{sid}/preview").json()
    assert r["kind"] == "fixed"
    assert r["window_start"].endswith("08:00:00+00:00")
    assert r["window_stop"].endswith("09:00:00+00:00")
