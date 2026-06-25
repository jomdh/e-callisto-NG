# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bench/commissioning operations over a BenchCapable driver (M12).

Thin orchestration of the ``BenchCapable`` primitives (ADR-0005) -- the legacy
``simple`` detector readout and the swept measurement that underlies the
NoiseFigurePlotter workflows. Pure of hardware: runs against any BenchCapable,
including the FakeDriver's synthetic detector.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from ecallisto_ng.core.contracts import BenchCapable


def _read_avg(driver: BenchCapable, integration: int) -> float:
    """Average ``integration`` detector reads at the current tune (C3)."""
    if integration <= 1:
        return driver.read_detector()
    total = sum(driver.read_detector() for _ in range(integration))
    return total / integration


def read_detector(
    driver: BenchCapable,
    frequency_mhz: float,
    gain: int,
    integration: int = 1,
) -> float:
    """Tune + set gain + read the detector; return millivolts (averaged)."""
    driver.set_gain(gain)
    driver.tune(frequency_mhz)
    return _read_avg(driver, integration)


def sweep(
    driver: BenchCapable,
    f_min: float,
    f_max: float,
    n_points: int,
    gain: int,
    relay: int | None = None,
    integration: int = 1,
    settle_s: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[tuple[float, float]]:
    """Sweep ``n_points`` frequencies; return ``(freq_mhz, mV)`` pairs.

    ``relay`` switches the focus/relay tree first (e.g. cold/warm/hot loads for
    a Y-factor measurement); ``settle_s`` waits for the relay to settle before
    reading (legacy preamble, audit C7). ``integration`` averages N reads per
    point (audit C3).
    """
    if n_points < 1:
        raise ValueError("n_points must be >= 1")
    if relay is not None:
        driver.set_relay(relay)
        if settle_s > 0:
            sleep(settle_s)
    driver.set_gain(gain)
    step = (f_max - f_min) / (n_points - 1) if n_points > 1 else 0.0
    out: list[tuple[float, float]] = []
    for i in range(n_points):
        freq = f_min + step * i
        driver.tune(freq)
        out.append((round(freq, 4), _read_avg(driver, integration)))
    return out


def agc_sweep(
    driver: BenchCapable,
    frequency_mhz: float,
    pwm_min: int = 0,
    pwm_max: int = 255,
    pwm_step: int = 5,
) -> list[tuple[int, float]]:
    """Sweep the AGC/PWM gain; return ``(pwm, mV)`` (legacy AGC plots, C5)."""
    if pwm_step < 1:
        raise ValueError("pwm_step must be >= 1")
    driver.tune(frequency_mhz)
    out: list[tuple[int, float]] = []
    for pwm in range(pwm_min, pwm_max + 1, pwm_step):
        driver.set_gain(pwm)
        out.append((pwm, driver.read_detector()))
    return out


def scope(
    driver: BenchCapable,
    frequency_mhz: float,
    gain: int,
    n_samples: int,
    threshold_mv: float | None = None,
) -> tuple[list[float], bool]:
    """Time-domain detector capture; return ``(samples_mv, triggered)`` (C6).

    Mirrors the legacy Digitizer/``simple`` scope: continuous detector reads at
    one tune, with an optional trigger threshold.
    """
    if n_samples < 1:
        raise ValueError("n_samples must be >= 1")
    driver.set_gain(gain)
    driver.tune(frequency_mhz)
    samples = [driver.read_detector() for _ in range(n_samples)]
    triggered = threshold_mv is not None and any(
        s >= threshold_mv for s in samples
    )
    return samples, triggered
