# SPDX-License-Identifier: AGPL-3.0-or-later
"""Export NG schedules to the legacy ``scheduler.cfg`` format (DESIGN 6a).

Lets an NG station keep feeding tools (or a legacy host) that expect the old
schedule file. Pure formatter.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# Legacy GenFrqPrg: 800 pixels/second total throughput (Unit1.cpp:54).
_PIX_PER_SEC = 800


@dataclass(frozen=True)
class ExportEntry:
    time_utc: str  # HH:MM[:SS]
    focus_code: int
    mode: str  # "3"=start, "0"=stop, "8"=overview (audit B1)
    program: str = ""  # 4th column: frqXXXXX.cfg program-switch


def build_scheduler_cfg(entries: Iterable[ExportEntry]) -> str:
    """Render ``hh:mm:ss,fc,mode[,fprog]`` lines (legacy header comment)."""
    lines = ["// scheduler.cfg exported by e-Callisto NG"]
    for e in sorted(entries, key=lambda x: x.time_utc):
        hhmmss = e.time_utc if len(e.time_utc) == 8 else f"{e.time_utc}:00"
        line = f"{hhmmss},{e.focus_code:02d},{e.mode}"
        if e.program:
            line += f",{e.program}"
        lines.append(line)
    return "\r\n".join(lines) + "\r\n"


def build_frequency_program_cfg(
    frequencies: Sequence[float],
    light_curve_indices: Iterable[int] = (),
    external_lo: float = 0.0,
    target: str = "CALLISTO",
) -> str:
    """Render a legacy ``frqXXXXX.cfg`` frequency program (audit D1).

    Includes the keys the legacy GenFrqPrg wrote (Unit1.cpp:273-339):
    ``[target]``, ``[on_line_testpoint_number]`` (= N/2),
    ``[number_of_measurements_per_sweep]`` (= N),
    ``[number_of_sweeps_per_second]`` (= 800/N), ``[external_lo]``, and one
    ``[NNNN]=FFFF.FFF,lc`` channel line each (with the light-curve flag).
    """
    n = len(frequencies)
    lc = set(light_curve_indices)
    sweeps = f"{_PIX_PER_SEC / n:g}" if n else "0"
    lines = [
        "// frequency program exported by e-Callisto NG",
        f"[target]={target}",
        f"[on_line_testpoint_number]={n // 2}",
        f"[number_of_measurements_per_sweep]={n}",
        f"[number_of_sweeps_per_second]={sweeps}",
        f"[external_lo]={external_lo:.3f}",
    ]
    for i, freq in enumerate(frequencies):
        flag = 1 if i in lc else 0
        lines.append(f"[{i + 1:04d}]={freq:08.3f},{flag}")
    return "\r\n".join(lines) + "\r\n"
