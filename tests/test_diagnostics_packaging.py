"""Device diagnostics endpoint + packaging artifacts present."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role

_ROOT = Path(__file__).resolve().parents[1]


def test_diagnose_probes_device(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "diag-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "diag-pass-1234"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "DIAG", "channels": 8}
    ).json()["id"]

    resp = client.get(f"/api/v1/instruments/{iid}/diagnose")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "FAKE"  # no address -> fake driver
    assert body["bit_depth"] == 8
    assert body["instrument_class"] == "heterodyne"


def test_systemd_unit_present() -> None:
    unit = _ROOT / "packaging" / "systemd" / "ecallisto-web.service"
    assert unit.exists()
    text = unit.read_text()
    assert "ExecStart=" in text
    assert "create_app --factory" in text


def test_install_script_present() -> None:
    script = _ROOT / "scripts" / "install.sh"
    assert script.exists()
    assert "systemctl enable" in script.read_text()
