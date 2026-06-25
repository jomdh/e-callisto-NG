"""Frequency-program generation (pure) + CRUD/generate API."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.freqgen import generate_frequencies


def test_generate_quiet_picks_minimum() -> None:
    # two points per 10 MHz bin; the quiet one has a much lower amplitude
    overview = [
        (100.0, 900.0),
        (105.0, 50.0),  # bin 100-110 -> pick 105
        (110.0, 40.0),
        (115.0, 800.0),  # bin 110-120 -> pick 110
    ]
    freqs = generate_frequencies(overview, 100.0, 120.0, 2, "quiet")
    assert freqs == [105.0, 110.0]


def test_generate_even_spacing() -> None:
    # even mode records the bin edge (D4), snapped to the 0.0625 grid
    freqs = generate_frequencies([], 0.0, 100.0, 4, "even")
    assert freqs == [0.0, 25.0, 50.0, 75.0]


def test_generate_validates() -> None:
    for bad in [
        lambda: generate_frequencies([], 0.0, 100.0, 0),
        lambda: generate_frequencies([], 100.0, 50.0, 4),
        lambda: generate_frequencies([], 0.0, 100.0, 4, "bogus"),
    ]:
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def _login(client: TestClient, role: Role) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, f"u_{role}", "prog-pass-1234", role)
    client.post(
        "/api/v1/auth/login",
        json={"username": f"u_{role}", "password": "prog-pass-1234"},
    )


def test_program_crud_and_generate(client: TestClient) -> None:
    _login(client, Role.OPERATOR)

    created = client.post(
        "/api/v1/programs",
        json={"name": "manual-1", "frequencies": [100.0, 200.0]},
    )
    assert created.status_code == 201
    assert created.json()["frequencies"] == [100.0, 200.0]

    gen = client.post(
        "/api/v1/programs/generate",
        json={
            "name": "gen-1",
            "overview": [[100.0, 10.0], [150.0, 5.0], [200.0, 8.0]],
            "start_mhz": 100.0,
            "stop_mhz": 200.0,
            "n_channels": 4,
            "mode": "quiet",
        },
    )
    assert gen.status_code == 201
    assert gen.json()["source"] == "generated"
    assert len(gen.json()["frequencies"]) == 4

    assert len(client.get("/api/v1/programs").json()) == 2


def test_program_rbac(client: TestClient) -> None:
    _login(client, Role.VIEWER)
    assert (
        client.post("/api/v1/programs", json={"name": "x"}).status_code == 403
    )
