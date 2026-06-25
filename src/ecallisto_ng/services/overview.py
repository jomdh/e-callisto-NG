# SPDX-License-Identifier: AGPL-3.0-or-later
"""Spectral overview / "radio monitoring" output (legacy parity, DESIGN 6).

The legacy recorder's "Save spectral overview" runs a wide 45-870 MHz sweep and
logs ``frequency;amplitude`` pairs to paired ``OVS_*.prn`` (semicolon) and
``.csv`` (comma) files. NG mirrors that: ``run_overview`` takes one overview
sweep from the driver and writes both files. Pure file writing in
``write_overview`` so it is testable without hardware.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from ecallisto_ng.core.contracts import InstrumentDriver

_BAND = (45.0, 870.0)


def _frequency_axis(n: int, band: tuple[float, float]) -> list[float]:
    if n <= 1:
        return [band[0]]
    span = band[1] - band[0]
    return [band[0] + span * i / (n - 1) for i in range(n)]


def write_overview(
    frequencies: Sequence[float],
    amplitudes: Sequence[int],
    out_dir: Path,
    instrument: str,
    when: datetime,
) -> tuple[Path, Path]:
    """Write the ``OVS_<instrument>_<ts>.prn`` + ``.csv`` pair."""
    base = f"OVS_{instrument}_{when:%Y%m%d_%H%M%S}"
    prn = out_dir / f"{base}.prn"
    csv = out_dir / f"{base}.csv"
    with prn.open("w") as fp, csv.open("w") as fc:
        fp.write("Freq[MHz];Amplitude\n")
        fc.write("Freq[MHz],Amplitude\n")
        for freq, amp in zip(frequencies, amplitudes, strict=False):
            fp.write(f"{freq:.4f};{amp}\n")
            fc.write(f"{freq:.4f},{amp}\n")
    return prn, csv


def run_overview(
    driver: InstrumentDriver,
    out_dir: Path,
    instrument: str,
    when: datetime,
    band: tuple[float, float] = _BAND,
) -> tuple[Path, Path]:
    """Take one overview sweep from the driver and write the OVS files."""
    driver.connect()
    try:
        frame = next(iter(driver.overview()))
    finally:
        driver.close()
    amplitudes = list(frame.values)
    frequencies = _frequency_axis(len(amplitudes), band)
    return write_overview(frequencies, amplitudes, out_dir, instrument, when)
