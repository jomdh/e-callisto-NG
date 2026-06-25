"""Offline map picker on the wizard coordinates step (M23 / F16)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_coordinates_step_has_map(client: TestClient) -> None:
    # step through: admin -> station -> coordinates
    client.post(
        "/wizard",
        data={"admin_username": "boss", "admin_password": "very-strong-pw"},
    )
    client.post("/wizard", data={"station_name": "MAP", "observatory": "Obs"})
    page = client.get("/wizard")
    assert "Step 3 of 5" in page.text  # coordinates
    assert 'id="map-canvas"' in page.text
    assert "/static/js/mappicker.js" in page.text
    # the map syncs the same lat/lon inputs the wizard posts
    assert 'id="latitude_deg"' in page.text
    assert 'id="longitude_deg"' in page.text


def test_map_picker_asset_served(client: TestClient) -> None:
    r = client.get("/static/js/mappicker.js")
    assert r.status_code == 200
    assert "equirectangular" in r.text or "toLat" in r.text
