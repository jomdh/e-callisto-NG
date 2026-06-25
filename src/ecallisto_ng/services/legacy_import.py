# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parse legacy e-Callisto config files for migration (DESIGN 9a).

Pure parsers for the legacy text formats (``callisto.cfg``, ``frqXXXXX.cfg``,
``scheduler.cfg``, ``CALxxxxx.prn``). The import route turns these into NG
records. Kept pure so the formats are exhaustively testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_KV = re.compile(r"\[(\w+)\]=(.*)")


def _kv_pairs(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _KV.match(line.strip())
        if m:
            out[m.group(1).lower()] = m.group(2).split("//")[0].strip()
    return out


@dataclass
class StationConfig:
    instrument: str = ""
    origin: str = ""
    titlecomment: str = ""
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    altitude_m: float = 0.0
    focus_code: int = 1
    gain: int = 120


def _signed(value: str, neg_codes: str) -> float:
    """Parse ``<code>,<number>`` (e.g. ``N,60.4``); negative for neg_codes."""
    parts = value.split(",")
    if len(parts) != 2:
        return 0.0
    code, num = parts[0].strip(), parts[1].strip()
    try:
        v = float(num)
    except ValueError:
        return 0.0
    return -v if code.upper() in neg_codes else v


def parse_callisto_cfg(text: str) -> StationConfig:
    kv = _kv_pairs(text)
    return StationConfig(
        instrument=kv.get("instrument", ""),
        origin=kv.get("origin", ""),
        titlecomment=kv.get("titlecomment", ""),
        latitude_deg=_signed(kv.get("latitude", ""), "S"),
        longitude_deg=_signed(kv.get("longitude", ""), "W"),
        altitude_m=float(kv.get("height", "0") or 0),
        focus_code=int(kv.get("focuscode", "1") or 1),
        gain=int(kv.get("agclevel", "120") or 120),
    )


@dataclass
class ProgramConfig:
    frequencies: list[float] = field(default_factory=list)
    sweeps_per_second: int = 4
    local_oscillator: float = 0.0


def parse_frequency_program(text: str) -> ProgramConfig:
    prog = ProgramConfig()
    indexed: list[tuple[int, float]] = []
    for line in text.splitlines():
        m = _KV.match(line.strip())
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2).split("//")[0].strip()
        if key == "number_of_sweeps_per_second":
            prog.sweeps_per_second = int(val or 4)
        elif key == "external_lo":
            prog.local_oscillator = float(val or 0)
        elif key.isdigit():
            freq = float(val.split(",")[0])
            indexed.append((int(key), freq))
    prog.frequencies = [f for _, f in sorted(indexed)]
    return prog


def parse_calibration_prn(text: str) -> list[list[float]]:
    """Return ``[a, b, cf, Tb]`` rows from a CAL file (skips the header)."""
    rows: list[list[float]] = []
    for line in text.splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        try:
            # channel, f_MHz, a, b, cf, Tb
            rows.append(
                [
                    float(parts[2]),
                    float(parts[3]),
                    float(parts[4]),
                    float(parts[5]),
                ]
            )
        except ValueError:
            continue
    return rows


@dataclass
class ScheduleEntry:
    time_utc: str  # HH:MM:SS
    focus_code: int
    mode: str  # single char: 0=stop, 8=overview, else=start (incl. A-Z)
    program: str = ""  # 4th column: frqXXXXX.cfg program-switch (audit B1)


def parse_scheduler_cfg(text: str) -> list[ScheduleEntry]:
    """Parse a legacy ``scheduler.cfg`` losslessly (audit B1).

    Keeps the mode as a single character (the legacy ``%1c`` accepts ``0-9``
    and ``A-Z``) and the optional 4th ``fprog`` program-switch column, instead
    of dropping them.
    """
    entries: list[ScheduleEntry] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or not line[0].isdigit():
            continue
        parts = line.split(",")
        if len(parts) < 3:
            continue
        try:
            focus = int(parts[1])
        except ValueError:
            continue
        mode = parts[2].strip()[:1].upper()
        if not mode:
            continue
        program = parts[3].strip() if len(parts) > 3 else ""
        entries.append(
            ScheduleEntry(
                time_utc=parts[0],
                focus_code=focus,
                mode=mode,
                program=program,
            )
        )
    return entries
