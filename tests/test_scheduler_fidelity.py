# SPDX-License-Identifier: AGPL-3.0-or-later
"""Scheduler fidelity vs SchedulerGeni/Scheduler.cpp (M27 B1-B3)."""

from __future__ import annotations

from datetime import date

from ecallisto_ng.services import legacy_import
from ecallisto_ng.services.legacy_export import (
    ExportEntry,
    build_scheduler_cfg,
)
from ecallisto_ng.services.scheduler import sun_window

_SCHED = "\n".join(
    [
        "06:30:00,01,3,frq00012.cfg",  # start + program-switch
        "12:00:00,01,A",  # alpha mode (legacy %1c)
        "19:30:00,01,8",  # scheduled overview
        "20:00:00,01,0",  # stop
    ]
)


def test_parse_keeps_mode_char_and_program() -> None:  # B1
    e = legacy_import.parse_scheduler_cfg(_SCHED)
    assert len(e) == 4  # alpha mode not dropped
    assert e[0].mode == "3" and e[0].program == "frq00012.cfg"
    assert e[1].mode == "A"  # A-Z preserved
    assert e[2].mode == "8" and e[3].mode == "0"


def test_export_emits_program_and_overview() -> None:  # B1 export
    cfg = build_scheduler_cfg(
        [
            ExportEntry("06:30", 1, "3", "frq00012.cfg"),
            ExportEntry("19:30", 1, "8"),
            ExportEntry("20:00", 1, "0"),
        ]
    )
    assert "06:30:00,01,3,frq00012.cfg" in cfg
    assert "19:30:00,01,8" in cfg


def test_horizon_trims_window() -> None:  # B2
    # equator at equinox: no-horizon window vs a 15-deg horizon (trims 1h/side)
    day = date(2026, 3, 21)
    flat = sun_window(0.0, 0.0, day, 0, 0.0)
    trimmed = sun_window(0.0, 0.0, day, 0, 15.0)
    assert flat is not None and trimmed is not None
    # 15 deg / 15 = 1 h later start, 1 h earlier stop
    assert (trimmed[0] - flat[0]).total_seconds() == 3600.0
    assert (flat[1] - trimmed[1]).total_seconds() == 3600.0


def test_sun_window_uses_standard_altitude() -> None:  # B3
    # a window exists at the equator equinox; events are near 06:00/18:00 UT
    win = sun_window(0.0, 0.0, date(2026, 3, 21), 0, 0.0)
    assert win is not None
    assert 5 <= win[0].hour <= 7
    assert 17 <= win[1].hour <= 19
