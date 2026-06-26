# SPDX-License-Identifier: AGPL-3.0-or-later
"""Station diagnostics self-check + report."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.diagnostics import run_self_check


def test_self_check_returns_overall_and_checks(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        rep = run_self_check(s)
    assert rep["status"] in ("ok", "warn", "fail")
    assert isinstance(rep["checks"], list) and rep["checks"]
    # every check is well-formed
    for c in rep["checks"]:
        assert c["status"] in ("ok", "warn", "fail")
        assert c["name"] and isinstance(c["detail"], str)


def test_diagnostics_endpoint(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "diag-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "diag-pass-1234"},
    )
    r = client.get("/api/v1/diagnostics")
    assert r.status_code == 200
    assert "checks" in r.json()
    # the downloadable report is plain text with the check lines
    rep = client.get("/api/v1/diagnostics/report")
    assert rep.status_code == 200
    assert "diagnostics report" in rep.text
    assert "attachment" in rep.headers.get("content-disposition", "")


def test_diagnostics_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/diagnostics").status_code == 401
