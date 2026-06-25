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

from ecallisto_ng import __version__
from ecallisto_ng.core.contracts import InstrumentDriver

_VERSION = f"e-CALLISTO NG {__version__}"
# Legacy amplitude window (mV) for a logged overview row (mainunit.cpp:340).
_AMP_MIN, _AMP_MAX = 50, 2500

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
    *,
    focus_code: int = 1,
    pwm: int = 0,
    title: str = "",
) -> tuple[Path, Path]:
    """Write the legacy ``OVS_<inst>_<title>_<ts>_<FCx>.prn`` + ``.csv`` pair.

    Byte-exact with the legacy recorder (audit B4): filename carries the title
    + focus code; the header records the PWM gain + version; rows are
    ``%7.3f;<amp>`` and gated to ``45 <= f <= 870`` and ``50 < amp < 2500``;
    the ``.csv`` uses the same semicolon layout the legacy code wrote.
    """
    base = f"OVS_{instrument}_{title}_{when:%Y%m%d_%H%M%S}_{focus_code:02d}"
    prn = out_dir / f"{base}.prn"
    csv = out_dir / f"{base}.csv"
    header = f"Frequency[MHz];Amplitude RX1[mV] at pwm={pwm};{_VERSION}\n"
    with prn.open("w") as fp, csv.open("w") as fc:
        fp.write(header)
        fc.write(header)
        for freq, amp in zip(frequencies, amplitudes, strict=False):
            if not (_BAND[0] <= freq <= _BAND[1]):
                continue
            if not (_AMP_MIN < amp < _AMP_MAX):
                continue
            line = f"{freq:7.3f};{amp}\n"
            fp.write(line)
            fc.write(line)
    return prn, csv


def run_overview(
    driver: InstrumentDriver,
    out_dir: Path,
    instrument: str,
    when: datetime,
    band: tuple[float, float] = _BAND,
    *,
    focus_code: int = 1,
    pwm: int = 0,
    title: str = "",
) -> tuple[Path, Path]:
    """Take one overview sweep from the driver and write the OVS files."""
    driver.connect()
    try:
        frame = next(iter(driver.overview()))
    finally:
        driver.close()
    amplitudes = list(frame.values)
    frequencies = _frequency_axis(len(amplitudes), band)
    return write_overview(
        frequencies,
        amplitudes,
        out_dir,
        instrument,
        when,
        focus_code=focus_code,
        pwm=pwm,
        title=title,
    )
