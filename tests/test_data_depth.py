"""Data browser depth: calendar, FITS header, bulk delete/requeue (M20)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role, UploadJob, UploadTarget
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.core import Channel, Recording, RecordingMeta, SpectrumFrame
from ecallisto_ng.services import catalog
from ecallisto_ng.writers.fits import StandardFitsWriter


def _write_fits(out_dir: Path, instrument: str, when: datetime) -> str:
    rec = Recording(
        meta=RecordingMeta(instrument=instrument),
        channels=(Channel(frequency_mhz=100.0), Channel(frequency_mhz=110.0)),
        frames=(
            SpectrumFrame(timestamp_utc=when, monotonic_ns=0, values=(10, 20)),
        ),
        sample_rate_hz=4.0,
    )
    return StandardFitsWriter().write(rec, out_dir).name


def test_recordings_by_day(tmp_path: Path) -> None:
    (tmp_path / "X_20260625_010000_01.fit").write_text("x")
    (tmp_path / "X_20260625_020000_01.fit").write_text("x")
    (tmp_path / "X_20260624_010000_01.fit").write_text("x")
    (tmp_path / "notafit.txt").write_text("x")
    counts = catalog.recordings_by_day(tmp_path)
    assert counts["2026-06-25"] == 2
    assert counts["2026-06-24"] == 1


def test_fits_header(tmp_path: Path) -> None:
    name = _write_fits(tmp_path, "HDRTEST", datetime(2026, 6, 25, tzinfo=UTC))
    hdr = catalog.fits_header(tmp_path / name)
    assert hdr.get("INSTRUME") == "HDRTEST"
    assert "NAXIS1" in hdr


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "data-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "data-pass-123"},
    )


def test_calendar_and_header_endpoints(client: TestClient) -> None:
    _login(client)
    data_dir = get_settings().data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    name = _write_fits(data_dir, "CAL", datetime(2026, 6, 25, tzinfo=UTC))

    cal = client.get("/api/v1/files/calendar").json()
    assert sum(cal.values()) >= 1

    hdr = client.get(f"/api/v1/files/{name}/header").json()
    assert hdr["INSTRUME"] == "CAL"


def test_bulk_delete_and_requeue(client: TestClient) -> None:
    _login(client)
    data_dir = get_settings().data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    keep = _write_fits(data_dir, "KEEP", datetime(2026, 6, 25, tzinfo=UTC))
    gone = _write_fits(data_dir, "GONE", datetime(2026, 6, 25, 1, tzinfo=UTC))

    with Session(db.get_engine()) as s:
        t = UploadTarget(name="t", protocol="local", host=str(data_dir))
        s.add(t)
        s.commit()
        s.refresh(t)
        s.add(UploadJob(filename=keep, target_id=t.id, state="done"))
        s.commit()

    # re-queue keep -> its done job is dropped
    rq = client.post(
        "/api/v1/files/bulk/requeue", json={"names": [keep]}
    ).json()
    assert rq["requeued"] == 1

    # delete gone -> file removed
    res = client.post(
        "/api/v1/files/bulk/delete", json={"names": [gone]}
    ).json()
    assert res["deleted"] == 1
    assert not (data_dir / gone).exists()
    assert (data_dir / keep).exists()


def test_data_page_renders_depth(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/data")
    assert page.status_code == 200
    assert "cal-heatmap" in page.text
    assert "bulk-delete" in page.text
    assert "/static/js/data.js" in page.text
