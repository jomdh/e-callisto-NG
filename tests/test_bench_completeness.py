# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bench completeness vs simple/NoiseFigurePlotter (M29 C3-C7)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.drivers.fake.driver import FakeDriver
from ecallisto_ng.services import bench, noise_figure


def test_scalar_gradient_matches_broadcast() -> None:  # C4
    cold = [10.0, 12.0, 11.0]
    hot = [40.0, 44.0, 42.0]
    # a scalar gradient must equal a per-point vector of the same constant
    nf_scalar = noise_figure.noise_figure(cold, hot, 2.0, 15.0)
    nf_vector = noise_figure.noise_figure(cold, hot, [2.0, 2.0, 2.0], 15.0)
    assert nf_scalar == nf_vector
    bp_scalar = noise_figure.bandpass(cold, hot, 2.0)
    bp_vector = noise_figure.bandpass(cold, hot, [2.0, 2.0, 2.0])
    assert bp_scalar == bp_vector


def test_integration_averages() -> None:  # C3
    d = FakeDriver(channels=8)
    d.connect()
    # integration > 1 returns a finite averaged reading
    mv = bench.read_detector(d, 150.0, 120, integration=4)
    assert isinstance(mv, float)
    d.close()


def test_settle_delay_injected() -> None:  # C7
    d = FakeDriver(channels=8)
    d.connect()
    calls: list[float] = []
    bench.sweep(
        d, 45.0, 60.0, 3, 120, relay=1, settle_s=0.5, sleep=calls.append
    )
    assert calls == [0.5]  # settle delay applied once after the relay switch
    d.close()


def test_agc_sweep() -> None:  # C5
    d = FakeDriver(channels=8)
    d.connect()
    pts = bench.agc_sweep(d, 150.0, 0, 255, 64)
    assert [p[0] for p in pts] == [0, 64, 128, 192]  # PWM steps
    assert all(isinstance(p[1], float) for p in pts)
    d.close()


def test_scope_trigger() -> None:  # C6
    d = FakeDriver(channels=8)
    d.connect()
    samples, triggered = bench.scope(d, 150.0, 120, 32, threshold_mv=-1.0)
    assert len(samples) == 32
    assert triggered is True  # threshold below any reading -> triggered
    _, untriggered = bench.scope(d, 150.0, 120, 32, threshold_mv=1e9)
    assert untriggered is False
    d.close()


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "bench-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "bench-pass-12"},
    )


def test_agc_and_scope_endpoints(client: TestClient) -> None:  # C5/C6
    _login(client)
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "BENCH", "instrument_class": "heterodyne"},
    ).json()["id"]
    agc = client.post(
        f"/api/v1/instruments/{iid}/bench/agc_sweep",
        json={"freq": 150.0, "pwm_step": 32},
    )
    assert agc.status_code == 200 and agc.json()["points"]
    scope = client.post(
        f"/api/v1/instruments/{iid}/bench/scope",
        json={"n_samples": 16, "threshold_mv": -1.0},
    )
    assert scope.status_code == 200
    assert len(scope.json()["samples"]) == 16


def test_noise_figure_scalar_gradient_endpoint(client: TestClient) -> None:
    _login(client)
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "NF", "instrument_class": "heterodyne"},
    ).json()["id"]
    r = client.post(
        f"/api/v1/instruments/{iid}/bench/noise_figure",
        json={"n_points": 8, "gradient": 5.0, "integration": 2},
    )
    assert r.status_code == 200
    assert "noise_figure" in r.json()
