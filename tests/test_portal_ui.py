"""Portal management pages render and are gated by login."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "ui-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "ui-pass-12345"},
    )


def test_pages_redirect_when_anonymous(client: TestClient) -> None:
    for path in (
        "/portal/manage/instruments",
        "/portal/access",
        "/portal/import",
        "/portal/fleet",
    ):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 303, path
        assert r.headers["location"] == "/"


def test_manage_pages_render(client: TestClient) -> None:
    _login(client)
    for resource in (
        "instruments",
        "schedules",
        "programs",
        "calibration",
        "uploads",
        "peers",
    ):
        r = client.get(f"/portal/manage/{resource}")
        assert r.status_code == 200, resource
        assert f'data-resource="{resource}"' in r.text
        assert "/static/js/console.js" in r.text
        assert "/portal/manage/schedules" in r.text  # nav present


def test_manage_unknown_resource_404(client: TestClient) -> None:
    _login(client)
    assert client.get("/portal/manage/bogus").status_code == 404


def test_settings_pages_render(client: TestClient) -> None:
    _login(client)
    assert "access-form" in client.get("/portal/access").text
    assert "import-form" in client.get("/portal/import").text
    assert "fleet-view" in client.get("/portal/fleet").text


def test_console_assets_served(client: TestClient) -> None:
    for asset in ("console.js", "settings.js"):
        r = client.get(f"/static/js/{asset}")
        assert r.status_code == 200
        assert "fetch" in r.text
