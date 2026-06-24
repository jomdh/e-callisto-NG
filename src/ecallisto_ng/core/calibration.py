"""Optional calibration: raw ADC -> SFU or antenna temperature (Kelvin).

Per-channel coefficients (a, b, cf, Tb) and the log-compression formulas ported
from the legacy ``FitsWrite.cpp``. Calibration is opt-in (DESIGN 6b): a
recording is raw unless a calibration is attached and a calibrated unit. Pure
math, no numpy, so it stays in ``core``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelCal:
    """Calibration coefficients for one channel."""

    a: float
    b: float
    cf: float
    tb: float


@dataclass(frozen=True)
class Calibration:
    """Per-channel coefficients, aligned with the recording's channels."""

    channels: tuple[ChannelCal, ...]


def _clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def to_sfu(adc: float, c: ChannelCal) -> int:
    """Raw ADC -> stored 8-bit value in the ``45*log(sfu+10)`` scale."""
    exponent = _clamp((adc - c.a) / c.b if c.b else 0.0, 0.43, 5.65)
    t_ant = math.pow(10.0, exponent)
    s = c.cf * (t_ant - c.tb)
    if s < -9.0:
        s = -9.0
    stored = 45.0 * math.log10(s + 10.0)
    return int(_clamp(stored, 0.0, 255.0))


def to_kelvin(adc: float, c: ChannelCal) -> int:
    """Raw ADC -> stored 8-bit value in the ``40*log(Tant)`` scale."""
    exponent = _clamp((adc - c.a) / c.b if c.b else 0.0, 0.43, 6.30)
    y = math.pow(10.0, exponent)
    t_ant = y * 290.0 - c.tb
    if t_ant < 2.7:
        t_ant = 2.7
    stored = 40.0 * math.log10(t_ant) + 0.5
    return int(_clamp(stored, 0.0, 255.0))
