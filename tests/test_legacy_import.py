"""Legacy parsers + import endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Instrument, Role, Station
from ecallisto_ng.services import legacy_import

_CFG = """\
[rxcomport]=COM18
[instrument]=ALASKA-COHOE
[origin]=COHOE
[titlecomment]=LWA-01
[latitude]=N,60.40
[longitude]=W,151.30
[height]=22
[focuscode]=01
[agclevel]=120
"""

_FRQ = """\
[number_of_measurements_per_sweep]=3
[number_of_sweeps_per_second]=4
[external_lo]=0.0
[0001]=45.000,0
[0002]=55.000,1
[0003]=65.000,0
"""

_CAL = """\
channel,f_MHz,a,b,cf,Tb
1,45.0,10.0,40.0,1.0,2.7
2,55.0,11.0,41.0,1.1,2.7
"""

_SCHED = """\
06:30:00,01,3
12:00:00,01,3
18:00:00,01,0
"""


def test_parse_callisto_cfg() -> None:
    cfg = legacy_import.parse_callisto_cfg(_CFG)
    assert cfg.instrument == "ALASKA-COHOE"
    assert cfg.latitude_deg == 60.4  # N -> positive
    assert cfg.longitude_deg == -151.3  # W -> negative
    assert cfg.altitude_m == 22.0
    assert cfg.focus_code == 1


def test_parse_frequency_program() -> None:
    prog = legacy_import.parse_frequency_program(_FRQ)
    assert prog.frequencies == [45.0, 55.0, 65.0]
    assert prog.sweeps_per_second == 4


def test_parse_calibration_prn() -> None:
    rows = legacy_import.parse_calibration_prn(_CAL)
    assert rows == [[10.0, 40.0, 1.0, 2.7], [11.0, 41.0, 1.1, 2.7]]


def test_parse_scheduler() -> None:
    entries = legacy_import.parse_scheduler_cfg(_SCHED)
    assert len(entries) == 3
    assert entries[0].mode == 3 and entries[2].mode == 0


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "import-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "import-pass-12"},
    )


def test_import_creates_records(client: TestClient) -> None:
    _login(client)
    resp = client.post(
        "/api/v1/import",
        json={
            "callisto_cfg": _CFG,
            "frq_cfg": _FRQ,
            "scheduler_cfg": _SCHED,
            "cal_prn": _CAL,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["instrument"] == "ALASKA-COHOE"
    assert body["program_channels"] == 3
    assert body["calibration_rows"] == 2

    with Session(db.get_engine()) as s:
        inst = s.exec(select(Instrument)).first()
        assert inst is not None and inst.name == "ALASKA-COHOE"
        assert inst.calibration_set_id is not None
        station = s.exec(select(Station)).first()
        assert station is not None and station.latitude_deg == 60.4


def test_import_dry_run_creates_nothing(client: TestClient) -> None:
    _login(client)
    resp = client.post(
        "/api/v1/import",
        json={"callisto_cfg": _CFG, "dry_run": True},
    )
    assert resp.json()["dry_run"] is True
    with Session(db.get_engine()) as s:
        assert s.exec(select(Instrument)).first() is None
