"""Sun-relative scheduler: ephemeris sanity + window logic + API."""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.scheduler import (
    is_recording_desired,
    sun_events,
    sun_window,
)


def test_sun_events_equator_equinox() -> None:
    # equator near equinox: rise ~06h, transit ~12h, set ~18h UTC
    ev = sun_events(0.0, 0.0, date(2026, 3, 20))
    assert ev.sunrise is not None and ev.sunset is not None
    assert ev.sunrise < ev.transit < ev.sunset
    assert 5 <= ev.sunrise.hour <= 7
    assert 11 <= ev.transit.hour <= 13
    assert 17 <= ev.sunset.hour <= 19


def test_sun_window_and_desire() -> None:
    window = sun_window(0.0, 0.0, date(2026, 3, 20))
    assert window is not None
    start, stop = window
    noon = datetime(2026, 3, 20, 12, tzinfo=UTC)
    midnight = datetime(2026, 3, 20, 0, tzinfo=UTC)
    assert is_recording_desired(window, noon)
    assert not is_recording_desired(window, midnight)


def test_schedule_api_and_preview(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "sched-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "sched-pass-123"},
    )
    # set up a station via the wizard path is overkill; create instrument first
    iid = client.post(
        "/api/v1/instruments", json={"name": "SCH", "channels": 8}
    ).json()["id"]
    created = client.post(
        "/api/v1/schedules",
        json={"instrument_id": iid, "kind": "sun", "margin_minutes": 15},
    )
    assert created.status_code == 201
    sid = created.json()["id"]

    prev = client.get(f"/api/v1/schedules/{sid}/preview")
    assert prev.status_code == 200
    body = prev.json()
    assert body["kind"] == "sun"
    assert "recording_now" in body
