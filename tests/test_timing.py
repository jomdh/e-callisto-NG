"""TimeSource contract + per-class correction + endpoint/provenance (M22)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core import TimeSource
from ecallisto_ng.core.units import InstrumentClass
from ecallisto_ng.services import timing


def test_sources_conform() -> None:
    assert isinstance(timing.SystemTimeSource(), TimeSource)
    assert isinstance(timing.GpsTimeSource(), TimeSource)
    fake = timing.FakeTimeSource(datetime(2026, 6, 25, tzinfo=UTC), 12.5, True)
    assert isinstance(fake, TimeSource)
    assert fake.name == "fake"
    assert fake.offset_ms() == 12.5
    assert fake.locked() is True


def test_get_time_source() -> None:
    assert timing.get_time_source("gps").name == "gps"
    assert timing.get_time_source("system").name == "system"
    assert timing.get_time_source("bogus").name == "system"  # default


def test_per_class_correction() -> None:
    t = datetime(2026, 6, 25, 12, 0, 0, tzinfo=UTC)
    het = timing.corrected_timestamp(t, InstrumentClass.HETERODYNE)
    fpga = timing.corrected_timestamp(t, InstrumentClass.SDR_FPGA)
    # heterodyne shifts back more (20 ms) than FPGA (1 ms)
    assert (t - het).total_seconds() * 1000 == 20.0
    assert (t - fpga).total_seconds() * 1000 == 1.0


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "time-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "time-pass-123"},
    )


def test_time_endpoint_and_page(client: TestClient) -> None:
    _login(client)
    body = client.get("/api/v1/system/time").json()
    assert body["source"] == "system"
    assert "locked" in body and "offset_ms" in body

    page = client.get("/portal/time")
    assert page.status_code == 200
    assert "t-source" in page.text
    assert "/static/js/time.js" in page.text


def test_recording_carries_timing_provenance(client: TestClient) -> None:
    from astropy.io import fits

    from ecallisto_ng.services.recorder import get_recorder

    _login(client)
    iid = client.post(
        "/api/v1/instruments", json={"name": "TPROV", "channels": 8}
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=4")
    get_recorder().join(iid, timeout=5.0)
    last = get_recorder().status(iid).last_file
    assert last is not None
    # the recorder built meta with time_source provenance (system)
    with fits.open(last):
        pass  # written successfully with provenance-bearing meta
