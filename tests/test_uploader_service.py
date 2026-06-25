"""Auto-dispatch (immediate) + retention pruning."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role, UploadTarget
from ecallisto_ng.services.recorder import get_recorder
from ecallisto_ng.services.uploader_service import UploaderService, prune


def _record_one(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "up-svc-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "up-svc-pass-12"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "AUP", "channels": 8}
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=5")
    get_recorder().join(iid, timeout=5.0)


def test_immediate_dispatch_uploads(
    client: TestClient, tmp_path: Path
) -> None:
    _record_one(client)
    mirror = tmp_path / "mirror"
    with Session(db.get_engine()) as s:
        s.add(
            UploadTarget(
                name="m",
                protocol="local",
                host=str(mirror),
                dispatch="immediate",
            )
        )
        s.commit()

    svc = UploaderService()
    now = datetime(2026, 6, 25, 12, tzinfo=UTC)
    with Session(db.get_engine()) as s:
        svc.tick(s, now)

    assert list(mirror.glob("*.fit.gz"))  # immediate target received the file


def test_retention_prunes_uploaded_only(
    client: TestClient, tmp_path: Path
) -> None:
    _record_one(client)
    mirror = tmp_path / "mirror"
    from ecallisto_ng.api.settings import get_settings

    data_dir = get_settings().data_dir
    before = list(data_dir.glob("*.fit"))
    assert len(before) == 1

    with Session(db.get_engine()) as s:
        s.add(
            UploadTarget(
                name="m",
                protocol="local",
                host=str(mirror),
                dispatch="immediate",
            )
        )
        s.commit()
        svc = UploaderService()
        svc.tick(s, datetime(2026, 6, 25, 12, tzinfo=UTC))
        # retention 0 days -> prune uploaded files immediately
        deleted = prune(s, data_dir, 0)

    assert deleted == 1
    assert not list(data_dir.glob("*.fit"))  # uploaded file pruned


def test_retention_keeps_unuploaded(
    client: TestClient, tmp_path: Path
) -> None:
    _record_one(client)
    from ecallisto_ng.api.settings import get_settings

    data_dir = get_settings().data_dir
    with Session(db.get_engine()) as s:
        s.add(
            UploadTarget(name="m", protocol="local", host=str(tmp_path / "m"))
        )
        s.commit()
        # no upload run -> file not uploaded -> retention must keep it
        deleted = prune(s, data_dir, 0)
    assert deleted == 0
    assert list(data_dir.glob("*.fit"))
