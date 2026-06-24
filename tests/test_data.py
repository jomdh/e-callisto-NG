"""Data browser: list, download, quicklook, traversal safety."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.recorder import get_recorder


def _login_and_record(client: TestClient) -> int:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "data-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "data-pass-1234"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "DATA", "channels": 8}
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=6")
    get_recorder().join(iid, timeout=5.0)
    return iid


def test_list_download_quicklook(client: TestClient) -> None:
    _login_and_record(client)

    files = client.get("/api/v1/files").json()
    assert len(files) == 1
    info = files[0]
    assert info["instrument"] == "DATA"
    assert info["rows"] == 8

    name = info["name"]
    dl = client.get(f"/api/v1/files/{name}/download")
    assert dl.status_code == 200
    assert dl.content[:6] == b"SIMPLE"  # FITS magic

    ql = client.get(f"/api/v1/files/{name}/quicklook")
    assert ql.status_code == 200
    assert ql.headers["content-type"] == "image/png"
    assert ql.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_download_rejects_traversal(client: TestClient) -> None:
    _login_and_record(client)
    assert (
        client.get("/api/v1/files/..%2f..%2fetc%2fpasswd/download").status_code
        == 404
    )
    assert client.get("/api/v1/files/nope.fit/download").status_code == 404


def test_data_page_renders(client: TestClient) -> None:
    _login_and_record(client)
    resp = client.get("/portal/data")
    assert resp.status_code == 200
    assert "Recorded files" in resp.text
