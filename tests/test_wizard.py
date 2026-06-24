"""First-run wizard: fresh install -> admin/station/instrument -> dashboard."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_fresh_install_routes_to_wizard(client: TestClient) -> None:
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/wizard"
    page = client.get("/wizard")
    assert page.status_code == 200
    assert "First-run setup" in page.text


def test_wizard_creates_and_logs_in(client: TestClient) -> None:
    resp = client.post(
        "/wizard",
        data={
            "admin_username": "boss",
            "admin_password": "very-strong-pw",
            "station_name": "ALASKA",
            "observatory": "Cohoe",
            "latitude_deg": "60.4",
            "longitude_deg": "-151.3",
            "altitude_m": "22",
            "instrument_name": "CALLISTO-01",
            "channels": "200",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "boss (admin)" in resp.text  # logged in on the dashboard
    assert "CALLISTO-01" in resp.text  # instrument created
    assert "ALASKA" in resp.text  # station named

    # already configured -> wizard redirects away
    again = client.get("/wizard", follow_redirects=False)
    assert again.status_code == 303
    assert again.headers["location"] == "/"


def test_wizard_blocked_after_setup(client: TestClient) -> None:
    client.post(
        "/wizard",
        data={"admin_username": "a", "admin_password": "pw-aaaaaa"},
        follow_redirects=True,
    )
    # a second submit must not create another admin
    blocked = client.post(
        "/wizard",
        data={"admin_username": "b", "admin_password": "pw-bbbbbb"},
        follow_redirects=False,
    )
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/"
