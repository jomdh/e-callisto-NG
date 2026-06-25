# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bench/commissioning operations over a BenchCapable driver (M12).

Thin orchestration of the ``BenchCapable`` primitives (ADR-0005) -- the legacy
``simple`` detector readout and the swept measurement that underlies the
NoiseFigurePlotter workflows. Pure of hardware: runs against any BenchCapable,
including the FakeDriver's synthetic detector.
"""

from __future__ import annotations

from ecallisto_ng.core.contracts import BenchCapable


def read_detector(
    driver: BenchCapable, frequency_mhz: float, gain: int
) -> float:
    """Tune + set gain + read the detector once; return millivolts."""
    driver.set_gain(gain)
    driver.tune(frequency_mhz)
    return driver.read_detector()


def sweep(
    driver: BenchCapable,
    f_min: float,
    f_max: float,
    n_points: int,
    gain: int,
    relay: int | None = None,
) -> list[tuple[float, float]]:
    """Sweep ``n_points`` frequencies; return ``(freq_mhz, mV)`` pairs.

    ``relay`` switches the focus/relay tree first (e.g. cold/warm/hot loads for
    a Y-factor measurement).
    """
    if n_points < 1:
        raise ValueError("n_points must be >= 1")
    if relay is not None:
        driver.set_relay(relay)
    driver.set_gain(gain)
    step = (f_max - f_min) / (n_points - 1) if n_points > 1 else 0.0
    out: list[tuple[float, float]] = []
    for i in range(n_points):
        freq = f_min + step * i
        driver.tune(freq)
        out.append((round(freq, 4), driver.read_detector()))
    return out
