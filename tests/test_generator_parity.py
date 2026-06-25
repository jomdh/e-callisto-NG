"""Generator LO/RFI math + upload connection test (M14)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.freqgen import generate_frequencies, rf_to_if


def test_exclude_band_keeps_channel_count() -> None:
    # even mode over 45-145, exclude 85-105: legacy keeps N, skips the gap (D5)
    freqs = generate_frequencies(
        [], 45.0, 145.0, 10, mode="even", exclude_band=(85.0, 105.0)
    )
    assert len(freqs) == 10  # channel count preserved (compaction)
    assert all(not (85.0 < f < 105.0) for f in freqs)  # nothing inside the gap


def test_quiet_avoids_rfi_points() -> None:
    overview = [(50.0, 5.0), (52.0, 1.0), (58.0, 9.0)]
    # 52 MHz is quietest but inside the RFI band -> not selected
    freqs = generate_frequencies(
        overview, 45.0, 55.0, 1, mode="quiet", exclude_band=(51.0, 53.0)
    )
    assert 52.0 not in freqs


def test_rf_to_if_converters() -> None:
    assert rf_to_if(200.0, 0.0, "direct") == 200.0
    assert rf_to_if(200.0, 150.0, "usb") == 50.0
    assert rf_to_if(200.0, 250.0, "lsb") == 50.0
    assert rf_to_if(200.0, 100.0, "up") == 300.0
    with pytest.raises(ValueError):
        rf_to_if(200.0, 0.0, "bogus")


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "gen-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "gen-pass-1234"},
    )


def test_generate_endpoint_excludes(client: TestClient) -> None:
    _login(client)
    r = client.post(
        "/api/v1/programs/generate",
        json={
            "name": "G",
            "overview": [],
            "start_mhz": 45.0,
            "stop_mhz": 145.0,
            "n_channels": 10,
            "mode": "even",
            "exclude_from": 85.0,
            "exclude_to": 105.0,
        },
    )
    assert r.status_code == 201
    freqs = r.json()["frequencies"]
    assert len(freqs) == 10  # keep-N (D5)
    assert all(not (85.0 < f < 105.0) for f in freqs)


def test_connection_test_endpoint(
    client: TestClient, tmp_path: object
) -> None:
    _login(client)
    ok = client.post(
        "/api/v1/upload/targets",
        json={"name": "L", "protocol": "local", "host": str(tmp_path)},
    ).json()["id"]
    r = client.post(f"/api/v1/upload/targets/{ok}/test")
    assert r.status_code == 200
    assert r.json()["ok"] is True  # local dir reachable
