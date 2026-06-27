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
    # The live viewer is the workspace Live tab now (ADR-0011); the old
    # /portal/live/{id} path redirects there for bookmarks.
    _login(client)
    iid = client.post(
        "/api/v1/instruments", json={"name": "LIVE", "channels": 16}
    ).json()["id"]
    redirect = client.get(f"/portal/live/{iid}", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == f"/portal/instruments/{iid}#live"

    page = client.get(f"/portal/instruments/{iid}")
    assert page.status_code == 200
    assert 'data-tab="live"' in page.text
    assert 'id="spectrum"' in page.text
    assert 'id="lightcurve"' in page.text
    assert 'id="live-db"' in page.text  # dB toggle


def test_d7_sfu_clamp_and_legacy_names(tmp_path: Path) -> None:  # D7
    lc = tmp_path / "LC20260625_SFU_ALASKA.txt"
    lc.write_text("Time_UT,100.000MHz\n0.0,99\n12.0,-50\n23.0,25\n")
    png = render_lightcurve_png(lc, tmp_path)
    assert png.name == "LC20260625_SFU_ALASKA.png"  # primary unchanged
    # legacy publication name + dated archive also written
    assert (tmp_path / "LightcurvesALASKA.png").exists()
    assert (tmp_path / "LightcurvesALASKA_20260625.png").exists()


def test_d7_unit_and_convert() -> None:  # D7
    from ecallisto_ng.services.lightcurve_png import _convert, _unit

    assert _unit("SFU") == "[SFU]"
    assert _unit("ADU") == "[dB]"
    # SFU clamps to [-10, 50]; ADU converts to dB via /25.4
    assert _convert([99.0, -50.0], "SFU") == [50.0, -10.0]
    assert _convert([25.4], "ADU") == [1.0]


def test_d6_viewer_has_mvdb_and_yrange(client: TestClient) -> None:  # D6
    _login(client)
    page = client.get("/portal/viewer")
    assert 'id="v-mvdb"' in page.text  # OVS mV->dB toggle
    assert 'id="v-ymin"' in page.text and 'id="v-ymax"' in page.text
    js = client.get("/static/js/viewer.js").text
    assert "/ 25.4" in js  # OVS mV->dB gradient
    assert "v-ymin" in js  # typed Y-range zoom
