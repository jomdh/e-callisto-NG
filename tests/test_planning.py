"""Observation planning: source track + endpoint + page (M23)."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role, Station
from ecallisto_ng.services import astro_track


def test_sun_track_shape_and_culmination() -> None:
    # mid-northern summer: the Sun should climb well above the horizon
    track = astro_track.source_track(
        47.0, 8.0, 500.0, date(2026, 6, 21), "sun", step_minutes=30
    )
    assert len(track) == 48  # 30-min steps over 24h
    elevations = [el for _, _, el in track]
    assert max(elevations) > 40.0  # high summer culmination
    assert min(elevations) < 0.0  # below horizon at night
    # az in [0, 360), el in [-90, 90]
    for _, az, el in track:
        assert 0.0 <= az < 360.0
        assert -90.0 <= el <= 90.0


def test_fixed_source_and_unknown() -> None:
    track = astro_track.source_track(
        47.0, 8.0, 500.0, date(2026, 6, 21), "cas_a"
    )
    assert len(track) == 48
    with pytest.raises(ValueError):
        astro_track.source_track(47.0, 8.0, 500.0, date(2026, 6, 21), "nope")


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        s.add(Station(latitude_deg=47.0, longitude_deg=8.0, horizon_deg=5.0))
        auth.create_user(s, "op", "plan-pass-12", Role.OPERATOR)
        s.commit()
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "plan-pass-12"},
    )


def test_track_endpoint(client: TestClient) -> None:
    _login(client)
    body = client.get("/api/v1/planning/track?source=sun").json()
    assert body["source"] == "sun"
    assert "sun" in body["sources"] and "cas_a" in body["sources"]
    assert body["horizon_deg"] == 5.0
    assert len(body["track"]) == 48
    assert len(body["track"][0]) == 3  # (hour, az, el)

    assert client.get("/api/v1/planning/track?source=bogus").status_code == 400


def test_planning_page(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/planning")
    assert page.status_code == 200
    assert "pl-canvas" in page.text
    assert "/static/js/planning.js" in page.text
    assert "/portal/planning" in page.text  # nav link
