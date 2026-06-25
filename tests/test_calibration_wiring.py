"""Calibration set -> calibrated recording; light-curve output."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from astropy.io import fits
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core import Channel, Recording, RecordingMeta, SpectrumFrame
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.services.lightcurve import write_light_curves
from ecallisto_ng.services.recorder import get_recorder


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "cal-wire-pass", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "cal-wire-pass"},
    )


def test_assigned_calibration_writes_sfu(client: TestClient) -> None:
    _login(client)
    cset = client.post(
        "/api/v1/calibration",
        json={"name": "c1", "coefficients": [[10.0, 40.0, 1.0, 2.7]]},
    ).json()
    iid = client.post(
        "/api/v1/instruments",
        json={
            "name": "CALW",
            "channels": 8,
            "unit": "sfu",
            "calibration_set_id": cset["id"],
        },
    ).json()["id"]

    client.post(f"/api/v1/instruments/{iid}/record?frames=5")
    get_recorder().join(iid, timeout=5.0)
    last = get_recorder().status(iid).last_file
    assert last is not None
    with fits.open(last) as hdul:
        assert hdul[0].header["BUNIT"] == "sfu"


def test_light_curves_written_for_flagged(tmp_path: Path) -> None:
    chans = (
        Channel(frequency_mhz=100.0, light_curve=True),
        Channel(frequency_mhz=200.0),
        Channel(frequency_mhz=300.0, light_curve=True),
    )
    frames = tuple(
        SpectrumFrame(
            timestamp_utc=datetime(2026, 6, 25, tzinfo=UTC),
            monotonic_ns=i,
            values=(10 + i, 20 + i, 30 + i),
        )
        for i in range(4)
    )
    rec = Recording(
        meta=RecordingMeta(instrument="LC"),
        channels=chans,
        frames=frames,
        sample_rate_hz=4.0,
        unit=UnitLevel.RAW,
    )
    path = write_light_curves(rec, tmp_path)
    assert path is not None and path.exists()
    lines = path.read_text().splitlines()
    assert lines[0] == "Time[UT.hours],100.000MHz,300.000MHz"  # flagged only
    assert len(lines) == 5  # header + 4 frames


def test_no_light_curves_when_none_flagged(tmp_path: Path) -> None:
    rec = Recording(
        meta=RecordingMeta(instrument="LC"),
        channels=(Channel(frequency_mhz=100.0),),
        frames=(
            SpectrumFrame(
                timestamp_utc=datetime(2026, 6, 25, tzinfo=UTC),
                monotonic_ns=0,
                values=(5,),
            ),
        ),
        sample_rate_hz=4.0,
    )
    assert write_light_curves(rec, tmp_path) is None
