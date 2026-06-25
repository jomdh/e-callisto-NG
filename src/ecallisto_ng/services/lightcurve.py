"""Light-curve product (legacy callisto.exe parity, DESIGN 6).

Channels flagged ``light_curve=True`` are written as the legacy daily file
``LC<YYYYMMDD>_<ADU|SFU|KEL>_<instrument>.txt``: comma-separated, a header
row of frequencies, then one timestamped row per sweep (fractional UT hours +
one value per flagged channel). At most **10** channels (legacy cap). Nothing
is written when no channel is flagged -- light curves are opt-in. Returns the
path or None.

The unit tag mirrors the legacy ``{ADU|SFU}`` naming; NG adds ``KEL`` for the
Kelvin product. The fractional-UT-hour time column feeds the 24-h UT
light-curve PNG renderer (wwwgeni parity, M13).
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from ecallisto_ng.core.recording import Recording
from ecallisto_ng.core.units import UnitLevel

MAX_LIGHT_CURVES = 10  # legacy ceiling

_UNIT_TAG = {
    UnitLevel.RAW: "ADU",
    UnitLevel.SFU: "SFU",
    UnitLevel.KELVIN: "KEL",
}


def _ut_hours(ts: datetime) -> float:
    return (
        ts.hour
        + ts.minute / 60.0
        + ts.second / 3600.0
        + ts.microsecond / 3.6e9
    )


def write_light_curves(recording: Recording, out_dir: Path) -> Path | None:
    flagged = [i for i, c in enumerate(recording.channels) if c.light_curve][
        :MAX_LIGHT_CURVES
    ]
    if not flagged:
        return None

    start = recording.frames[0].timestamp_utc
    tag = _UNIT_TAG.get(recording.unit, "ADU")
    name = f"LC{start:%Y%m%d}_{tag}_{recording.meta.instrument}.txt"
    path = out_dir / name
    header = ["Time[UT.hours]"] + [
        f"{recording.channels[i].frequency_mhz:.3f}MHz" for i in flagged
    ]
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for frame in recording.frames:
            row: list[object] = [round(_ut_hours(frame.timestamp_utc), 6)]
            row += [frame.values[i] for i in flagged]
            writer.writerow(row)
    return path
