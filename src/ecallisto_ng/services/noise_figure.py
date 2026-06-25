# SPDX-License-Identifier: AGPL-3.0-or-later
"""Noise-figure / detector-slope / bandpass math (legacy NF.cpp parity, M12).

Pure functions over aligned cold/warm/hot detector sweeps (millivolts per
frequency). Mirrors the Y-factor formulas from ``NoiseFigurePlotter`` so the
results match the legacy bench instrument. No hardware: the sweeps are produced
by ``services.bench.sweep`` against any BenchCapable driver.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import log10

# A per-point measured slope vector, or a single scalar detector gradient
# (mV/dB) -- the legacy NF.cpp uses one config constant (audit C4).
SlopeLike = Sequence[float] | float


def _slopes(slope: SlopeLike, n: int) -> list[float]:
    """Broadcast a scalar gradient to ``n`` points, or pass a vector."""
    if isinstance(slope, (int, float)):
        return [float(slope)] * n
    return list(slope)


@dataclass(frozen=True)
class Stat:
    mean: float
    sigma: float


def stats(values: Sequence[float]) -> Stat:
    if not values:
        return Stat(0.0, 0.0)
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return Stat(round(mean, 4), round(var**0.5, 4))


def detector_slope(
    warm: Sequence[float], hot: Sequence[float], att_db: float
) -> list[float]:
    """Detector sensitivity per point in mV/dB: ``|hot - warm| / att``."""
    if att_db == 0:
        raise ValueError("att_db must be non-zero")
    return [abs(h - w) / att_db for w, h in zip(warm, hot, strict=False)]


def noise_figure(
    cold: Sequence[float],
    hot: Sequence[float],
    slope_mv_db: SlopeLike,
    enr_db: float,
) -> list[float]:
    """Y-factor noise figure per point (dB).

    ``ydb = |hot-cold| / slope``; ``ylin = 10^(ydb/10)``;
    ``NF = ENR - 10*log10(ylin - 0.999)`` (the legacy guard avoids log(<=0)).
    ``slope_mv_db`` is a per-point vector or a single scalar gradient (C4).
    """
    slopes = _slopes(slope_mv_db, len(cold))
    out: list[float] = []
    for c, h, g in zip(cold, hot, slopes, strict=False):
        if g <= 0:
            out.append(0.0)
            continue
        ylin = 10.0 ** ((abs(h - c) / g) / 10.0)
        out.append(enr_db - 10.0 * log10(ylin - 0.999) if ylin > 1.0 else 0.0)
    return out


def bandpass(
    cold: Sequence[float],
    hot: Sequence[float],
    slope_mv_db: SlopeLike,
) -> list[float]:
    """Overall bandpass (dB), normalized so the passband peak is 0 dB.

    ``slope_mv_db`` is a per-point vector or a single scalar gradient (C4).
    """
    slopes = _slopes(slope_mv_db, len(cold))
    raw = [
        (abs(h - c) / g if g > 0 else 0.0)
        for c, h, g in zip(cold, hot, slopes, strict=False)
    ]
    peak = max(raw) if raw else 0.0
    return [round(r - peak, 4) for r in raw]
