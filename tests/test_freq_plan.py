# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-instrument frequency plan: resolver + frq import + binding (M32)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import (
    FrequencyProgram,
    Instrument,
    Role,
)
from ecallisto_ng.services.channels import resolve_channels


def test_resolver_precedence(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        prog_a = FrequencyProgram(
            name="A", frequencies_json=json.dumps([100.0, 200.0])
        )
        prog_b = FrequencyProgram(
            name="B", frequencies_json=json.dumps([300.0, 400.0, 500.0])
        )
        s.add(prog_a)
        s.add(prog_b)
        s.commit()
        s.refresh(prog_a)
        s.refresh(prog_b)
        inst = Instrument(name="I", channels=8, program_id=prog_a.id)
        s.add(inst)
        s.commit()

        # instrument's program -> its frequencies
        ch = resolve_channels(s, inst)
        assert [c.frequency_mhz for c in ch] == [100.0, 200.0]
        # explicit override (e.g. a schedule's program) wins
        ch2 = resolve_channels(s, inst, program_id=prog_b.id)
        assert [c.frequency_mhz for c in ch2] == [300.0, 400.0, 500.0]
        # no program -> 45+N ramp
        inst.program_id = None
        ch3 = resolve_channels(s, inst)
        assert len(ch3) == 8
        assert ch3[0].frequency_mhz == 45.0


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "plan-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "plan-pass-123"},
    )


def test_generate_in_range_then_bind(client: TestClient) -> None:
    _login(client)
    pid = client.post(
        "/api/v1/programs/generate",
        json={
            "name": "R1",
            "overview": [],
            "start_mhz": 45.0,
            "stop_mhz": 870.0,
            "n_channels": 50,
            "mode": "even",
        },
    ).json()["id"]
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "BOUND", "program_id": pid},
    ).json()["id"]
    got = client.get(f"/api/v1/instruments/{iid}").json()
    assert got["program_id"] == pid  # the plan is bound to the instrument


def test_import_frq_file(client: TestClient) -> None:
    _login(client)
    frq = (
        "[target]=CALLISTO\n"
        "[number_of_measurements_per_sweep]=3\n"
        "[external_lo]=0.000\n"
        "[0001]=0045.000,0\n"
        "[0002]=0100.000,1\n"
        "[0003]=0200.000,0\n"
    )
    r = client.post(
        "/api/v1/programs/import/frq", json={"name": "fromfrq", "text": frq}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["frequencies"] == [45.0, 100.0, 200.0]
    assert body["start_mhz"] == 45.0 and body["stop_mhz"] == 200.0
