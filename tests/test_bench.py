"""BenchCapable contract + detector readout + sweep (M12 / ADR-0005)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core import BenchCapable
from ecallisto_ng.drivers.callisto import CallistoDriver
from ecallisto_ng.drivers.callisto.protocol import parse_detector
from ecallisto_ng.drivers.callisto.simulator import SimulatedCallisto
from ecallisto_ng.drivers.fake import FakeDriver
from ecallisto_ng.drivers.sdr import SoftSdrDriver
from ecallisto_ng.services import bench as bench_svc


def test_bench_capability_detection() -> None:
    assert isinstance(FakeDriver(), BenchCapable)
    assert isinstance(CallistoDriver(SimulatedCallisto()), BenchCapable)
    # an SDR driver does not implement bench primitives
    assert not isinstance(SoftSdrDriver(), BenchCapable)


def test_parse_detector_reply() -> None:
    assert parse_detector("$CRX:ADC0=1234\r") == 1234.0
    assert parse_detector("noise") is None


def test_detector_responds_to_freq_and_gain() -> None:
    d = FakeDriver(channels=8)
    on_band = bench_svc.read_detector(d, 150.0, 200)  # passband centre
    off_band = bench_svc.read_detector(d, 800.0, 200)
    low_gain = bench_svc.read_detector(d, 150.0, 20)
    assert on_band > off_band  # bandpass shape
    assert on_band > low_gain  # gain scales the reading
    assert 0.0 <= on_band <= 2600.0


def test_sweep_shape_and_relay() -> None:
    d = FakeDriver(channels=8)
    points = bench_svc.sweep(d, 45.0, 870.0, n_points=20, gain=200)
    assert len(points) == 20
    assert points[0][0] == 45.0 and points[-1][0] == 870.0
    # relay offset shifts the whole sweep up
    hot = bench_svc.sweep(d, 45.0, 870.0, 20, 200, relay=63)
    assert hot[0][1] > points[0][1]


def _login(client: TestClient) -> int:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "bench-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "bench-pass-12"},
    )
    return client.post(
        "/api/v1/instruments",
        json={"name": "BENCH", "instrument_class": "heterodyne"},
    ).json()["id"]


def test_bench_endpoints(client: TestClient) -> None:
    iid = _login(client)
    det = client.get(
        f"/api/v1/instruments/{iid}/bench/detector?freq=150&gain=200"
    )
    assert det.status_code == 200
    assert det.json()["mv"] > 0

    sweep = client.post(
        f"/api/v1/instruments/{iid}/bench/sweep",
        json={"f_min": 45, "f_max": 870, "n_points": 10, "gain": 200},
    )
    assert sweep.status_code == 200
    assert len(sweep.json()["points"]) == 10


def test_bench_rejects_non_bench_instrument(client: TestClient) -> None:
    _login(client)
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "SDRX", "instrument_class": "sdr_soft"},
    ).json()["id"]
    r = client.get(f"/api/v1/instruments/{iid}/bench/detector")
    assert r.status_code == 400
