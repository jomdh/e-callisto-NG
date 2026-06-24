"""Upload: local transport + uploader idempotence + API run."""

from __future__ import annotations

import gzip
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core.contracts import UploadTransport
from ecallisto_ng.services.recorder import get_recorder
from ecallisto_ng.services.uploader import upload_file
from ecallisto_ng.transports.local import LocalTransport


def test_local_transport_conforms() -> None:
    assert isinstance(LocalTransport("/tmp/x"), UploadTransport)


def test_upload_file_gzips(tmp_path: Path) -> None:
    src = tmp_path / "rec.fit"
    src.write_bytes(b"SIMPLE  =  T" + b"\x00" * 100)
    dest = tmp_path / "dest"
    upload_file(LocalTransport(str(dest)), src, "rec.fit.gz", do_gzip=True)
    out = dest / "rec.fit.gz"
    assert out.exists()
    with gzip.open(out, "rb") as fh:
        assert fh.read() == src.read_bytes()


def _login_record(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "up-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "up-pass-12345"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "UP", "channels": 8}
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=5")
    get_recorder().join(iid, timeout=5.0)


def test_run_target_uploads_then_skips(
    client: TestClient, tmp_path: Path
) -> None:
    _login_record(client)
    dest = tmp_path / "mirror"
    target = client.post(
        "/api/v1/upload/targets",
        json={"name": "mirror", "protocol": "local", "host": str(dest)},
    ).json()
    tid = target["id"]

    first = client.post(f"/api/v1/upload/targets/{tid}/run").json()
    assert first["uploaded"] == 1 and first["failed"] == 0
    assert list(dest.glob("*.fit.gz"))

    # second run: already uploaded -> nothing new
    second = client.post(f"/api/v1/upload/targets/{tid}/run").json()
    assert second["uploaded"] == 0

    queue = client.get("/api/v1/upload/queue").json()
    assert len(queue) == 1 and queue[0]["state"] == "done"
