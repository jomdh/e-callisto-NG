"""First-run multi-step resumable wizard (M18)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from httpx import Response


def test_fresh_install_routes_to_wizard(client: TestClient) -> None:
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/wizard"
    page = client.get("/wizard")
    assert page.status_code == 200
    assert "Step 1 of 5" in page.text  # admin step
    assert "Administrator" in page.text


def test_wizard_resumes_mid_flow(client: TestClient) -> None:
    # step 0 (admin) -> advances to step 1 (station), persisted
    client.post(
        "/wizard",
        data={"admin_username": "boss", "admin_password": "very-strong-pw"},
    )
    page = client.get("/wizard")
    assert "Step 2 of 5" in page.text  # resumed at station
    assert "Station" in page.text


def _complete(client: TestClient, instrument: str = "CALLISTO-01") -> Response:
    client.post(
        "/wizard",
        data={"admin_username": "boss", "admin_password": "very-strong-pw"},
    )
    client.post(
        "/wizard", data={"station_name": "ALASKA", "observatory": "Cohoe"}
    )
    client.post(
        "/wizard",
        data={
            "latitude_deg": "60.4",
            "longitude_deg": "-151.3",
            "altitude_m": "22",
        },
    )
    client.post(
        "/wizard",
        data={
            "instrument_name": instrument,
            "instrument_class": "heterodyne",
            "channels": "200",
        },
    )
    return client.post("/wizard", data={}, follow_redirects=True)  # review


def test_wizard_completes_and_logs_in(client: TestClient) -> None:
    resp = _complete(client)
    assert resp.status_code == 200
    assert "boss (admin)" in resp.text  # logged in on the dashboard
    assert "CALLISTO-01" in resp.text  # instrument created
    assert "ALASKA" in resp.text  # station named

    again = client.get("/wizard", follow_redirects=False)
    assert again.status_code == 303
    assert again.headers["location"] == "/"


def test_wizard_blocked_after_setup(client: TestClient) -> None:
    _complete(client)
    blocked = client.post(
        "/wizard",
        data={"admin_username": "b", "admin_password": "pw-bbbbbb"},
        follow_redirects=False,
    )
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/"


def test_wizard_legacy_import_branch(client: TestClient) -> None:
    # admin step first, then paste a callisto.cfg on the station step
    client.post(
        "/wizard",
        data={"admin_username": "boss", "admin_password": "very-strong-pw"},
    )
    client.post(
        "/wizard",
        data={
            "callisto_cfg": (
                "[instrument]=ALASKA-COHOE\n"
                "[origin]=COHOE\n"
                "[latitude]=N,60.40\n"
                "[longitude]=W,151.30\n"
                "[height]=22\n"
            )
        },
    )
    # jumped to review, pre-filled from the cfg
    review = client.get("/wizard")
    assert "Step 5 of 5" in review.text
    assert "ALASKA-COHOE" in review.text

    done = client.post("/wizard", data={}, follow_redirects=True)
    assert "ALASKA-COHOE" in done.text  # imported instrument created
