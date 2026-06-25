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

# Tuner synthesizer step (MHz); channels snap to this grid (audit D4).
SYNTHESIZER_RESOLUTION = 0.0625


def _snap(freq: float) -> float:
    """Snap a frequency to the 0.0625 MHz synthesizer grid (legacy)."""
    step = SYNTHESIZER_RESOLUTION
    return round(round(freq / step) * step, 4)


def _excluded(band: tuple[float, float] | None, freq: float) -> bool:
    # half-open [lo, hi): the upper edge is allowed (it is the first channel
    # past the RFI gap when keeping the channel count).
    return band is not None and band[0] <= freq < band[1]


def generate_frequencies(
    overview: Sequence[OverviewPoint],
    start_mhz: float,
    stop_mhz: float,
    n_channels: int,
    mode: str = "quiet",
    exclude_band: tuple[float, float] | None = None,
    nonlinear_start: int = 0,
) -> list[float]:
    """Return ``n_channels`` frequencies (MHz) selected across the band.

    ``exclude_band`` removes an RFI band: the channel count is **kept** by
    distributing channels over the band minus the excluded width and stepping
    past the gap (legacy GenFrqPrg compaction, audit D5). ``nonlinear_start``
    pins the first N channels to ``start_mhz`` (audit D2). Selections snap to
    the 0.0625 MHz synthesizer grid (D4).
    """
    if n_channels < 1:
        raise ValueError("n_channels must be >= 1")
    if stop_mhz <= start_mhz:
        raise ValueError("stop must exceed start")
    if mode not in ("quiet", "even"):
        raise ValueError(f"unknown mode: {mode}")
    if not 0 <= nonlinear_start < n_channels:
        raise ValueError("nonlinear_start must be in [0, n_channels)")

    points = sorted(overview)
    result: list[float] = [_snap(start_mhz)] * nonlinear_start  # D2

    linear_n = n_channels - nonlinear_start
    excl_w = 0.0
    if exclude_band is not None:
        lo_c = max(exclude_band[0], start_mhz)
        hi_c = min(exclude_band[1], stop_mhz)
        excl_w = max(0.0, hi_c - lo_c)
    step = (stop_mhz - start_mhz - excl_w) / max(linear_n, 1)

    freq = start_mhz
    for _ in range(linear_n):
        if exclude_band is not None and _excluded(exclude_band, freq):
            freq = exclude_band[
                1
            ]  # skip past the RFI gap, keep the count (D5)
        lo, hi = freq, freq + step
        if mode == "even":
            sel = lo  # legacy records the bin edge, not the centre (D4)
        else:  # quiet: lowest-amplitude non-RFI point in the bin, else edge
            window = [
                p
                for p in points
                if lo <= p[0] < hi and not _excluded(exclude_band, p[0])
            ]
            sel = min(window, key=lambda p: p[1])[0] if window else lo
        result.append(_snap(sel))
        freq += step
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
