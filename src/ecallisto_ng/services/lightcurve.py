"""Light-curve product: per-channel time series for flagged channels.

A recording's channels flagged ``light_curve=True`` are written as a CSV
(time + one column per flagged frequency). If no channel is flagged, nothing is
written (light curves are opt-in, DESIGN 6). Returns the path or None.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ecallisto_ng.core.recording import Recording


def write_light_curves(recording: Recording, out_dir: Path) -> Path | None:
    flagged = [i for i, c in enumerate(recording.channels) if c.light_curve]
    if not flagged:
        return None

    start = recording.frames[0].timestamp_utc
    name = f"LC_{recording.meta.instrument}_{start:%Y%m%d_%H%M%S}.csv"
    path = out_dir / name
    dt = 1.0 / recording.sample_rate_hz if recording.sample_rate_hz else 0.0
    header = ["time_s"] + [
        f"{recording.channels[i].frequency_mhz:.3f}MHz" for i in flagged
    ]
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for n, frame in enumerate(recording.frames):
            row = [round(n * dt, 4)] + [frame.values[i] for i in flagged]
            writer.writerow(row)
    return path
