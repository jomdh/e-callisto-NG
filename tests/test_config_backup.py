"""Config backup/restore + system info + settings page (M15)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import FrequencyProgram, Instrument, Role
from ecallisto_ng.services import config_backup


def test_export_import_round_trip(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        s.add(Instrument(name="A", channels=8))
        s.add(FrequencyProgram(name="P", frequencies_json="[45.0, 50.0]"))
        s.commit()
        snapshot = config_backup.export_config(s)
        assert len(snapshot["instruments"]) == 1
        assert len(snapshot["programs"]) == 1

    # wipe + restore
    with Session(db.get_engine()) as s:
        for inst in s.exec(select(Instrument)).all():
            s.delete(inst)
        s.commit()
        assert s.exec(select(Instrument)).first() is None
        counts = config_backup.import_config(s, snapshot)
        assert counts["instruments"] == 1
        restored = s.exec(select(Instrument)).all()
        assert [i.name for i in restored] == ["A"]


def _admin(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "boss", "admin-pass-1", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "boss", "password": "admin-pass-1"},
    )


def test_system_info(client: TestClient) -> None:
    _admin(client)
    info = client.get("/api/v1/system/info").json()
    assert "version" in info
    assert info["disk_total"] > 0
    assert "clock_synced" in info


def test_config_endpoints(client: TestClient) -> None:
    _admin(client)
    client.post("/api/v1/instruments", json={"name": "EXP", "channels": 4})
    backup = client.get("/api/v1/config/export").json()
    assert any(i["name"] == "EXP" for i in backup["instruments"])

    restored = client.post("/api/v1/config/import", json=backup)
    assert restored.status_code == 200
    assert restored.json()["instruments"] >= 1


def test_config_admin_only(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "op-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "op-pass-12345"},
    )
    assert client.get("/api/v1/config/export").status_code == 403


def test_settings_page_renders(client: TestClient) -> None:
    _admin(client)
    page = client.get("/portal/settings")
    assert page.status_code == 200
    assert "cfg-export" in page.text
    assert "sysinfo" in page.text
