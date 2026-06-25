"""2-column spectrum parsing + spectra endpoints + viewer page (M13)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import spectrum


def test_parse_delimiters() -> None:
    # comma, semicolon, space -- all auto-detected, one header line skipped
    for sep in (",", ";", " "):
        text = f"Freq{sep}Amp\n45.0{sep}10\n50.0{sep}20\n"
        freqs, amps = spectrum.parse_two_column(text)
        assert freqs == [45.0, 50.0]
        assert amps == [10.0, 20.0]


def test_parse_skips_bad_rows() -> None:
    text = "h1,h2\n45.0,10\nbad line\n50.0,20\n"
    freqs, amps = spectrum.parse_two_column(text)
    assert freqs == [45.0, 50.0]


def test_list_spectra(tmp_path: Path) -> None:
    (tmp_path / "OVS_X_1.prn").write_text("h\n45;1\n")
    (tmp_path / "a.csv").write_text("h\n1,2\n")
    (tmp_path / "ignore.fit").write_text("x")
    names = spectrum.list_spectra(tmp_path)
    assert "OVS_X_1.prn" in names and "a.csv" in names
    assert "ignore.fit" not in names


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "view-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "view-pass-123"},
    )


def test_spectra_endpoints(client: TestClient) -> None:
    _login(client)
    data_dir = get_settings().data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "OVS_T_20260625_120000.prn").write_text(
        "Freq[MHz];Amplitude\n45.0000;100\n870.0000;50\n"
    )
    names = client.get("/api/v1/spectra").json()
    assert "OVS_T_20260625_120000.prn" in names

    spec = client.get("/api/v1/spectra/OVS_T_20260625_120000.prn").json()
    assert spec["freqs"] == [45.0, 870.0]
    assert spec["amps"] == [100.0, 50.0]

    assert client.get("/api/v1/spectra/../etc.prn").status_code in (404, 400)


def test_viewer_page_renders(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal/viewer")
    assert page.status_code == 200
    assert "v-canvas" in page.text
    assert "/static/js/viewer.js" in page.text
    assert "/portal/viewer" in page.text  # nav link
