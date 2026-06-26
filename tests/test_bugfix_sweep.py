# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression tests for the v0.10.1 bug-hunt sweep."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core import Channel, RecordingMeta
from ecallisto_ng.core.spectra import SpectrumFrame
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.writers.fits.standard import StandardFitsWriter, _unique_path


def _op(client: TestClient) -> None:
    with __import__("sqlmodel").Session(db.get_engine()) as s:
        auth.create_user(s, "op", "bugfix-pass-12", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "bugfix-pass-12"},
    )


def test_duplicate_names_are_409_not_500(client: TestClient) -> None:
    _op(client)
    # one representative of each create route that had the unhandled-unique bug
    cases = [
        ("/api/v1/calibration", {"name": "d", "coefficients": []}),
        (
            "/api/v1/upload/targets",
            {"name": "d", "kind": "ftp", "host": "h", "remote_dir": "/"},
        ),
        ("/api/v1/alerts/channels", {"name": "d", "kind": "webhook"}),
        ("/api/v1/fleet/peers", {"name": "d", "base_url": "http://x"}),
    ]
    for url, body in cases:
        r1 = client.post(url, json=body)
        assert r1.status_code in (200, 201), (url, r1.status_code, r1.text)
        r2 = client.post(url, json=body)
        assert r2.status_code == 409, (url, r2.status_code, r2.text)


def test_bad_fk_is_4xx_not_500(client: TestClient) -> None:
    _op(client)
    # instrument referencing a non-existent program -> clean 409, not 500
    r = client.post(
        "/api/v1/instruments", json={"name": "i", "program_id": 99999}
    )
    assert r.status_code == 409


def test_invalid_role_is_422_not_500(client: TestClient) -> None:
    with __import__("sqlmodel").Session(db.get_engine()) as s:
        auth.create_user(s, "admin", "bugfix-pass-12", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "bugfix-pass-12"},
    )
    r = client.post(
        "/api/v1/users",
        json={"username": "x", "password": "y", "role": "superuser"},
    )
    assert r.status_code == 422


def _frame(v: list[int], t: datetime) -> SpectrumFrame:
    return SpectrumFrame(timestamp_utc=t, monotonic_ns=0, values=v)


def test_fits_write_never_overwrites_same_second(tmp_path: Path) -> None:
    w = StandardFitsWriter()
    ch = (Channel(frequency_mhz=45.0), Channel(frequency_mhz=46.0))
    meta = RecordingMeta(instrument="X", focus_code=1)
    t = datetime(2026, 6, 26, 10, 0, 0, tzinfo=UTC)

    from ecallisto_ng.core.recording import Recording

    def rec(vals: list[int]) -> Recording:
        return Recording(
            meta=meta,
            channels=ch,
            frames=(_frame(vals, t), _frame(vals, t)),
            sample_rate_hz=4.0,
            unit=UnitLevel.RAW,
        )

    p1 = w.write(rec([1, 2]), tmp_path)
    p2 = w.write(rec([3, 4]), tmp_path)  # same UT second -> must NOT overwrite
    assert p1 != p2
    assert p1.exists() and p2.exists()
    # no leftover .tmp files
    assert not list(tmp_path.glob("*.tmp"))


def test_unique_path_suffixes() -> None:
    assert _unique_path(Path("/nope/x.fit")) == Path("/nope/x.fit")
