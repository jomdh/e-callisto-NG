# SPDX-License-Identifier: AGPL-3.0-or-later
"""frqXXXXX.cfg export + grid snap vs GenFrqPrg (M28 D1/D4)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.freqgen import _snap, generate_frequencies
from ecallisto_ng.services.legacy_export import build_frequency_program_cfg


def test_frq_cfg_has_legacy_keys() -> None:  # D1
    cfg = build_frequency_program_cfg(
        [45.0, 100.0, 200.0, 400.0],
        light_curve_indices=[1, 3],
        external_lo=0.0,
    )
    assert "[target]=CALLISTO" in cfg
    assert "[number_of_measurements_per_sweep]=4" in cfg
    assert "[number_of_sweeps_per_second]=200" in cfg  # 800 / 4
    assert "[on_line_testpoint_number]=2" in cfg  # N // 2
    assert "[external_lo]=0.000" in cfg
    # channel lines: 1-based index, %08.3f, light-curve flag
    assert "[0001]=0045.000,0" in cfg
    assert "[0002]=0100.000,1" in cfg  # flagged
    assert "[0004]=0400.000,1" in cfg


def test_grid_snap() -> None:  # D4
    assert _snap(45.03) == 45.0  # nearest 0.0625
    assert _snap(45.0625) == 45.0625
    # generated frequencies are all on the 0.0625 grid
    freqs = generate_frequencies([], 45.0, 870.0, 50, mode="even")
    for f in freqs:
        assert abs(round(f / 0.0625) * 0.0625 - f) < 1e-6


def test_even_mode_uses_bin_edge() -> None:  # D4
    freqs = generate_frequencies([], 45.0, 85.0, 4, mode="even")
    # step 10 MHz, edges 45/55/65/75 (snapped); not centres 50/60/70/80
    assert freqs[0] == 45.0


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "frq-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "frq-pass-123"},
    )


def test_frq_export_endpoint(client: TestClient) -> None:
    _login(client)
    pid = client.post(
        "/api/v1/programs",
        json={
            "name": "P1",
            "frequencies": [45.0, 60.0, 75.0],
            "light_curve_indices": [0],
        },
    ).json()["id"]
    r = client.get(f"/api/v1/programs/{pid}/export/frq")
    assert r.status_code == 200
    assert "[target]=CALLISTO" in r.text
    assert "[0001]=0045.000,1" in r.text  # channel 0 flagged


def test_nonlinear_start_pins_channels() -> None:  # D2
    freqs = generate_frequencies(
        [], 45.0, 145.0, 10, mode="even", nonlinear_start=3
    )
    assert len(freqs) == 10
    assert freqs[0] == freqs[1] == freqs[2] == 45.0  # first 3 pinned to start
    assert freqs[-1] > 45.0  # the linear sweep progresses up the band


def test_keep_n_with_exclusion() -> None:  # D5
    freqs = generate_frequencies(
        [], 45.0, 145.0, 10, mode="even", exclude_band=(85.0, 105.0)
    )
    assert len(freqs) == 10  # channel count preserved
    assert all(not (85.0 < f < 105.0) for f in freqs)


def test_generate_endpoint_converter(client: TestClient) -> None:  # D3
    _login(client)
    r = client.post(
        "/api/v1/programs/generate",
        json={
            "name": "DC",
            "overview": [],
            "start_mhz": 1200.0,  # RF above the Callisto IF -> downconverter
            "stop_mhz": 1800.0,
            "n_channels": 8,
            "mode": "even",
            "converter": "usb",
            "local_oscillator": 1155.0,  # IF = RF - LO lands in 45-870
        },
    )
    assert r.status_code == 201  # no RF limit; converter maps it (user config)
    assert len(r.json()["frequencies"]) == 8
