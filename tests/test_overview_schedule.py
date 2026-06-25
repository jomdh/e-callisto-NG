"""Overview OVS output + scheduler program-switch / scheduled overview."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from sqlmodel import Session

from ecallisto_ng.api import db
from ecallisto_ng.api.models import (
    FrequencyProgram,
    Instrument,
    Schedule,
    Station,
)
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.drivers.fake import FakeDriver
from ecallisto_ng.services.overview import run_overview, write_overview
from ecallisto_ng.services.recorder import get_recorder
from ecallisto_ng.services.scheduler_service import SchedulerService


def test_write_overview_pair(tmp_path: Path) -> None:
    prn, csv = write_overview(
        [45.0, 100.0, 870.0],
        [100, 200, 300],  # all within the 50<amp<2500 gate
        tmp_path,
        "ALASKA",
        datetime(2026, 6, 25, 17, 30, tzinfo=UTC),
        focus_code=1,
        pwm=120,
    )
    # legacy filename: OVS_<inst>_<title>_<ts>_<FCx> (audit B4)
    assert prn.name == "OVS_ALASKA__20260625_173000_01.prn"
    assert csv.name == "OVS_ALASKA__20260625_173000_01.csv"
    prn_lines = prn.read_text().splitlines()
    assert prn_lines[0].startswith(
        "Frequency[MHz];Amplitude RX1[mV] at pwm=120;"
    )
    assert prn_lines[1] == f"{45.0:7.3f};100"  # %7.3f, semicolon
    # legacy wrote the same semicolon layout to the .csv too
    assert csv.read_text().splitlines()[1] == f"{45.0:7.3f};100"


def test_overview_amplitude_gate(tmp_path: Path) -> None:
    # amplitudes outside 50<amp<2500 (or freq outside 45-870) are dropped
    prn, _ = write_overview(
        [45.0, 100.0, 200.0],
        [10, 200, 3000],  # 10 too low, 3000 too high -> only the middle kept
        tmp_path,
        "GATE",
        datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
    )
    rows = prn.read_text().splitlines()[1:]
    assert len(rows) == 1
    assert rows[0] == f"{100.0:7.3f};200"


def test_run_overview_from_driver(tmp_path: Path) -> None:
    prn, csv = run_overview(
        FakeDriver(channels=32),
        tmp_path,
        "FAKE",
        datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
    )
    assert prn.exists() and csv.exists()
    lines = prn.read_text().splitlines()
    # header + at most 32 rows (some may be gated out by amplitude)
    assert 1 <= len(lines) <= 1 + 32
    assert lines[0].startswith("Frequency[MHz];")


def _instrument(s: Session) -> int:
    inst = Instrument(name="SCHED", channels=8, sweep_rate_hz=4.0)
    s.add(inst)
    s.commit()
    s.refresh(inst)
    assert inst.id is not None
    return inst.id


def test_scheduler_uses_program_channels(client: object) -> None:
    captured: dict[str, object] = {}
    real_start = get_recorder().start

    def _spy(
        instrument_id: int,
        driver: object,
        channels: object,
        *args: object,
        **kwargs: object,
    ) -> None:
        captured["channels"] = channels

    get_recorder().start = _spy  # type: ignore[method-assign]
    try:
        with Session(db.get_engine()) as s:
            iid = _instrument(s)
            prog = FrequencyProgram(
                name="P1",
                frequencies_json=json.dumps([50.0, 60.0, 70.0]),
                light_curve_indices_json=json.dumps([1]),
            )
            s.add(prog)
            s.commit()
            s.refresh(prog)
            s.add(
                Schedule(
                    instrument_id=iid,
                    kind="fixed",
                    start_utc="00:00",
                    stop_utc="23:59",
                    program_id=prog.id,
                )
            )
            s.add(Station())
            s.commit()
            SchedulerService().tick(
                s, datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
            )
    finally:
        get_recorder().start = real_start  # type: ignore[method-assign]

    chans = cast(list[Channel], captured["channels"])
    assert [c.frequency_mhz for c in chans] == [50.0, 60.0, 70.0]
    assert [c.light_curve for c in chans] == [False, True, False]


def test_scheduled_overview_runs_once_per_day(client: object) -> None:
    data_dir = get_settings().data_dir
    with Session(db.get_engine()) as s:
        iid = _instrument(s)
        s.add(
            Schedule(
                instrument_id=iid,
                kind="fixed",
                start_utc="06:00",
                stop_utc="07:00",  # window closed at 17:30 -> not recording
                overview_at="17:00",
            )
        )
        s.add(Station())
        s.commit()
        svc = SchedulerService()
        when = datetime(2026, 6, 25, 17, 30, tzinfo=UTC)
        svc.tick(s, when)
        ovs = list(data_dir.glob("OVS_SCHED_*.prn"))
        assert len(ovs) == 1
        # second tick same day -> no new overview
        svc.tick(s, datetime(2026, 6, 25, 17, 45, tzinfo=UTC))
        assert len(list(data_dir.glob("OVS_SCHED_*.prn"))) == 1
