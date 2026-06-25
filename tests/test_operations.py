"""Operations cockpit: per-instrument status + dashboard cards (M20)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import (
    Instrument,
    Role,
    Schedule,
    Station,
)
from ecallisto_ng.services.operations import instrument_cockpit


def test_cockpit_fields_and_next_action(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        inst = Instrument(name="OPX", channels=8)
        s.add(inst)
        s.add(Station())
        s.commit()
        s.refresh(inst)
        s.add(
            Schedule(
                instrument_id=inst.id,
                kind="fixed",
                start_utc="06:00",
                stop_utc="18:00",
            )
        )
        s.commit()
        # noon -> inside the window -> "recording until 18:00"
        rows = instrument_cockpit(s, datetime(2026, 6, 25, 12, 0, tzinfo=UTC))
        row = next(r for r in rows if r["name"] == "OPX")
        assert row["state"] == "idle"  # not actually recording
        assert "until 18:00" in row["next_action"]
        assert row["channels"] == 8

        # before the window -> "next start 06:00"
        rows = instrument_cockpit(s, datetime(2026, 6, 25, 3, 0, tzinfo=UTC))
        row = next(r for r in rows if r["name"] == "OPX")
        assert "next start 06:00" in row["next_action"]


def test_no_schedule_action(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        s.add(Instrument(name="NOSCH", channels=4))
        s.add(Station())
        s.commit()
        rows = instrument_cockpit(s, datetime(2026, 6, 25, tzinfo=UTC))
        row = next(r for r in rows if r["name"] == "NOSCH")
        assert row["next_action"] == "no schedule"


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "ops-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "ops-pass-1234"},
    )


def test_operations_endpoint(client: TestClient) -> None:
    _login(client)
    client.post("/api/v1/instruments", json={"name": "EP", "channels": 8})
    body = client.get("/api/v1/operations").json()
    assert "instruments" in body
    assert "disk_pct_free" in body
    assert body["instruments"][0]["name"] == "EP"
    assert "next_action" in body["instruments"][0]


def test_dashboard_renders_cockpit_cards(client: TestClient) -> None:
    _login(client)
    client.post("/api/v1/instruments", json={"name": "DASH", "channels": 8})
    page = client.get("/portal")
    assert page.status_code == 200
    assert "cockpit-card" in page.text
    assert "cockpit-wf" in page.text  # mini-waterfall canvas
    assert 'data-act="record"' in page.text
    assert "/static/js/dashboard.js" in page.text
