"""Clock probe + recording gate + debian packaging artifacts."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.clock import clock_synced, may_record

_ROOT = Path(__file__).resolve().parents[1]


def test_clock_synced_tristate() -> None:
    # never raises; bool or None (None where timedatectl is absent, e.g. macOS)
    assert clock_synced() in (True, False, None)


def test_may_record_gate() -> None:
    assert may_record(False, False) is True  # not required -> always ok
    assert may_record(False, None) is True
    assert may_record(True, True) is True
    assert may_record(True, None) is True  # unknown -> allowed
    assert may_record(True, False) is False  # required + known-bad -> blocked


def test_health_includes_clock(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "clock-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "clock-pass-12"},
    )
    body = client.get("/api/v1/system/health").json()
    assert "clock_synced" in body


def test_debian_packaging_present() -> None:
    deb = _ROOT / "packaging" / "debian"
    for name in ("control", "rules", "postinst", "changelog"):
        assert (deb / name).exists(), name
    assert "Package: ecallisto-ng" in (deb / "control").read_text()
    assert "adduser" in (deb / "postinst").read_text()
