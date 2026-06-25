# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frequency-program generation from a spectral overview.

Ports the GenFrqPrg idea (DESIGN 8.2 / legacy analysis): split the band into N
steps and pick one channel per step. ``quiet`` mode picks the lowest-amplitude
(least-RFI) point in each step; ``even`` mode picks evenly spaced frequencies.
Pure and testable -- no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence

OverviewPoint = tuple[float, float]  # (frequency_mhz, amplitude)


def _excluded(band: tuple[float, float] | None, freq: float) -> bool:
    return band is not None and band[0] <= freq <= band[1]


def generate_frequencies(
    overview: Sequence[OverviewPoint],
    start_mhz: float,
    stop_mhz: float,
    n_channels: int,
    mode: str = "quiet",
    exclude_band: tuple[float, float] | None = None,
) -> list[float]:
    """Return frequencies (MHz) selected across the band.

    ``exclude_band`` removes an RFI band (legacy GenFrqPrg exclusion): bins
    centred inside it are dropped, and quiet-mode selection ignores points in
    it -- so the result may have fewer than ``n_channels`` entries.
    """
    if n_channels < 1:
        raise ValueError("n_channels must be >= 1")
    if stop_mhz <= start_mhz:
        raise ValueError("stop must exceed start")
    if mode not in ("quiet", "even"):
        raise ValueError(f"unknown mode: {mode}")

    points = sorted(overview)
    step = (stop_mhz - start_mhz) / n_channels
    result: list[float] = []
    for i in range(n_channels):
        lo = start_mhz + i * step
        hi = lo + step
        center = lo + step / 2.0
        if _excluded(exclude_band, center):
            continue  # RFI-excluded bin
        if mode == "even":
            freq = center
        else:  # quiet: lowest-amplitude non-RFI point in the bin, else center
            window = [
                p
                for p in points
                if lo <= p[0] < hi and not _excluded(exclude_band, p[0])
            ]
            freq = min(window, key=lambda p: p[1])[0] if window else center
        result.append(round(freq, 3))
    return result


def rf_to_if(rf_mhz: float, local_oscillator: float, converter: str) -> float:
    """Convert a desired RF to the IF the receiver tunes (legacy LO math).

    ``direct``: IF=RF; ``usb``: IF=RF-LO; ``lsb``: IF=LO-RF; ``up``: IF=RF+LO.
    """
    if converter == "direct":
        return rf_mhz
    if converter == "usb":
        return rf_mhz - local_oscillator
    if converter == "lsb":
        return local_oscillator - rf_mhz
    if converter == "up":
        return rf_mhz + local_oscillator
    raise ValueError(f"unknown converter: {converter}")
