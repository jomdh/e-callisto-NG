"""Public light-curve PNG renderer + endpoints + live panels (M13)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services.lightcurve_png import render_lightcurve_png

_LC = (
    "Time[UT.hours],100.000MHz,200.000MHz\n"
    "6.0,10,20\n"
    "12.0,30,15\n"
    "18.0,12,40\n"
)


def test_render_lightcurve_png(tmp_path: Path) -> None:
    lc = tmp_path / "LC20260625_ADU_ALASKA.txt"
    lc.write_text(_LC)
    png = render_lightcurve_png(lc, tmp_path)
    assert png.name == "LC20260625_ADU_ALASKA.png"
    with Image.open(png) as img:
        assert img.size == (800, 496)
        assert img.mode == "RGB"


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "lcpng-pass-1", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "lcpng-pass-1"},
    )


def test_lightcurve_endpoints(client: TestClient) -> None:
    _login(client)
    data_dir = get_settings().data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "LC20260625_SFU_X.txt").write_text(_LC)

    names = client.get("/api/v1/lightcurves").json()
    assert "LC20260625_SFU_X.txt" in names

    png = client.get("/api/v1/lightcurves/LC20260625_SFU_X.txt/png")
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic


def test_live_page_has_panels(client: TestClient) -> None:
    _login(client)
    iid = client.post(
        "/api/v1/instruments", json={"name": "LIVE", "channels": 16}
    ).json()["id"]
    page = client.get(f"/portal/live/{iid}")
    assert page.status_code == 200
    assert 'id="spectrum"' in page.text
    assert 'id="lightcurve"' in page.text
    assert 'id="live-db"' in page.text  # dB toggle
