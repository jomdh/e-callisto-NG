"""Noise-figure math + endpoint + Tools page (M12)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services import noise_figure as nf


def test_detector_slope() -> None:
    slope = nf.detector_slope([100.0, 100.0], [200.0, 150.0], att_db=10.0)
    assert slope == [10.0, 5.0]  # |hot-warm|/att


def test_noise_figure_and_bandpass() -> None:
    cold = [100.0, 100.0, 100.0]
    hot = [300.0, 250.0, 200.0]
    slope = [10.0, 10.0, 10.0]
    vals = nf.noise_figure(cold, hot, slope, enr_db=15.0)
    assert len(vals) == 3
    assert all(v < 15.0 for v in vals)  # NF below ENR for these Y-factors
    bp = nf.bandpass(cold, hot, slope)
    assert max(bp) == 0.0  # normalized: peak at 0 dB
    assert bp[0] == 0.0 and bp[2] < 0.0  # falls off from the peak


def test_stats() -> None:
    s = nf.stats([2.0, 4.0, 6.0])
    assert s.mean == 4.0
    assert round(s.sigma, 3) == 1.633


def test_nf_guards_zero_slope() -> None:
    assert nf.noise_figure([1.0], [2.0], [0.0], 15.0) == [0.0]


def _login(client: TestClient) -> int:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "nf-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "nf-pass-12345"},
    )
    return client.post(
        "/api/v1/instruments",
        json={"name": "NF", "instrument_class": "heterodyne"},
    ).json()["id"]


def test_noise_figure_endpoint(client: TestClient) -> None:
    iid = _login(client)
    r = client.post(
        f"/api/v1/instruments/{iid}/bench/noise_figure",
        json={"n_points": 16, "enr_db": 15.0, "att_db": 10.1},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["freqs"]) == 16
    assert len(body["noise_figure"]) == 16
    assert "nf_mean" in body and "bandpass_db" in body


def test_tools_redirects_to_instruments(client: TestClient) -> None:
    # Bench moved into the per-instrument workspace (ADR-0011); the old
    # standalone /portal/tools redirects operators to pick an instrument.
    _login(client)
    r = client.get("/portal/tools", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/portal/manage/instruments"
