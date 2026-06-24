"""Frequency-program generation from a spectral overview.

Ports the GenFrqPrg idea (DESIGN 8.2 / legacy analysis): split the band into N
steps and pick one channel per step. ``quiet`` mode picks the lowest-amplitude
(least-RFI) point in each step; ``even`` mode picks evenly spaced frequencies.
Pure and testable -- no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence

OverviewPoint = tuple[float, float]  # (frequency_mhz, amplitude)


def generate_frequencies(
    overview: Sequence[OverviewPoint],
    start_mhz: float,
    stop_mhz: float,
    n_channels: int,
    mode: str = "quiet",
) -> list[float]:
    """Return ``n_channels`` frequencies (MHz) selected across the band."""
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
        if mode == "even":
            freq = center
        else:  # quiet: lowest-amplitude point in the bin, else bin center
            window = [p for p in points if lo <= p[0] < hi]
            freq = min(window, key=lambda p: p[1])[0] if window else center
        result.append(round(freq, 3))
    return result
