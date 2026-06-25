# SPDX-License-Identifier: AGPL-3.0-or-later
"""Export NG schedules to the legacy ``scheduler.cfg`` format (DESIGN 6a).

Lets an NG station keep feeding tools (or a legacy host) that expect the old
schedule file. Pure formatter.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


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
