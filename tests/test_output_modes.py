"""Legacy output mode (writer + comments) + scheduler.cfg export."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from astropy.io import fits
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role, Schedule
from ecallisto_ng.core import Channel, Recording, RecordingMeta, SpectrumFrame
from ecallisto_ng.services.legacy_export import (
    ExportEntry,
    build_scheduler_cfg,
)
from ecallisto_ng.writers.fits import (
    LegacyFitsWriter,
    StandardFitsWriter,
    get_writer,
)


def _recording() -> Recording:
    return Recording(
        meta=RecordingMeta(instrument="OM"),
        channels=(Channel(frequency_mhz=100.0), Channel(frequency_mhz=110.0)),
        frames=(
            SpectrumFrame(
                timestamp_utc=datetime(2026, 6, 25, tzinfo=UTC),
                monotonic_ns=0,
                values=(10, 20),
            ),
        ),
        sample_rate_hz=4.0,
    )


def test_get_writer_modes() -> None:
    assert isinstance(get_writer("legacy"), LegacyFitsWriter)
    assert isinstance(get_writer("standard"), StandardFitsWriter)
    assert isinstance(get_writer("custom"), StandardFitsWriter)  # MVP


def test_legacy_writer_adds_comments(tmp_path: Path) -> None:
    std = tmp_path / "std"
    leg = tmp_path / "leg"
    std.mkdir()
    leg.mkdir()
    std_path = StandardFitsWriter().write(_recording(), std)
    leg_path = LegacyFitsWriter().write(_recording(), leg)
    with fits.open(std_path) as s, fits.open(leg_path) as g:
        std_comments = str(s[0].header.get("COMMENT", ""))
        leg_comments = str(g[0].header.get("COMMENT", ""))
        assert "CDELT1 may be rounded" not in std_comments
        assert "CDELT1 may be rounded" in leg_comments


def test_build_scheduler_cfg() -> None:
    out = build_scheduler_cfg(
        [ExportEntry("18:00", 1, "0"), ExportEntry("06:30", 1, "3")]
    )
    lines = out.strip().splitlines()
    assert lines[0].startswith("//")
    assert lines[1] == "06:30:00,01,3"  # sorted by time
    assert lines[2] == "18:00:00,01,0"


def test_export_endpoint(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "mode-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "mode-pass-123"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "EXP", "channels": 8}
    ).json()["id"]
    with Session(db.get_engine()) as s:
        s.add(
            Schedule(
                instrument_id=iid,
                kind="fixed",
                start_utc="06:00",
                stop_utc="18:00",
            )
        )
        s.commit()
    resp = client.get("/api/v1/schedules/export/scheduler.cfg")
    assert resp.status_code == 200
    assert "06:00:00,01,3" in resp.text
    assert "18:00:00,01,0" in resp.text
