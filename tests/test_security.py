"""B2 credential encryption + CSP (the M7 release gate)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.crypto import decrypt, encrypt
from ecallisto_ng.api.models import Role, UploadTarget


def test_crypto_round_trip() -> None:
    assert decrypt(encrypt("hunter2")) == "hunter2"
    assert encrypt("") == "" and decrypt("") == ""
    assert encrypt("hunter2") != "hunter2"  # not plaintext


def _login_operator(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "sec-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "sec-pass-12345"},
    )


def test_credentials_encrypted_and_not_leaked(client: TestClient) -> None:
    _login_operator(client)
    created = client.post(
        "/api/v1/upload/targets",
        json={
            "name": "ftp1",
            "protocol": "ftp",
            "host": "ftp.example.org",
            "username": "u",
            "password": "topsecret",
        },
    )
    assert created.status_code == 201
    body = created.json()
    # response carries no password, only a flag
    assert "password" not in body
    assert body["has_password"] is True

    # stored value is ciphertext, not the plaintext
    with Session(db.get_engine()) as s:
        row = s.exec(select(UploadTarget)).first()
        assert row is not None
        assert row.password != "topsecret"
        assert decrypt(row.password) == "topsecret"

    # listing also omits the secret
    listed = client.get("/api/v1/upload/targets").json()
    assert "password" not in listed[0]


def test_csp_header_and_nonce(client: TestClient) -> None:
    _login_operator(client)
    resp = client.get("/portal", follow_redirects=True)
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "script-src 'self' 'nonce-" in csp
    # the inline theme-bootstrap script carries the matching nonce
    nonce = csp.split("'nonce-")[1].split("'")[0]
    assert f'nonce="{nonce}"' in resp.text
