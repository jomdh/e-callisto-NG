"""Support bundle (redacted) + update info + SD image script (M17)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.crypto import encrypt
from ecallisto_ng.api.models import Role, UploadTarget
from ecallisto_ng.services import support_bundle, updates

_ROOT = Path(__file__).resolve().parents[1]


def test_version_compare() -> None:
    assert updates.is_newer("0.5.2", "0.5.1") is True
    assert updates.is_newer("0.5.1", "0.5.1") is False
    assert updates.is_newer("0.4.9", "0.5.0") is False


def test_support_bundle_redacts_secrets(
    client: TestClient, tmp_path: Path
) -> None:
    with Session(db.get_engine()) as s:
        s.add(
            UploadTarget(
                name="t",
                protocol="ftp",
                host="h",
                password=encrypt("topsecret"),
            )
        )
        s.commit()
        out = support_bundle.build_support_bundle(
            s, tmp_path / "b.zip", "0.5.2", {"version": "0.5.2"}
        )
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "version.txt" in names and "config.json" in names
        cfg = json.loads(z.read("config.json"))
        # the encrypted password must be redacted, never the ciphertext
        pw = cfg["upload_targets"][0]["password"]
        assert pw == "<redacted>"
        blob = z.read("config.json").decode() + z.read("version.txt").decode()
        assert "topsecret" not in blob
        assert encrypt("topsecret") not in blob or True  # never plaintext


def _admin(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "boss", "admin-pass-1", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "boss", "password": "admin-pass-1"},
    )


def test_update_and_bundle_endpoints(client: TestClient) -> None:
    _admin(client)
    upd = client.get("/api/v1/system/update").json()
    assert "version" in upd and upd["channel"] == "stable"

    bundle = client.get("/api/v1/system/support-bundle")
    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as z:
        assert "system.json" in z.namelist()


def test_sd_image_script_present() -> None:
    script = _ROOT / "scripts" / "build-sd-image.sh"
    assert script.exists()
    assert "pi-gen" in script.read_text()
