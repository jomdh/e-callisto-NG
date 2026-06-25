"""Build a core ``Calibration`` from a stored ``CalibrationSet`` row."""

from __future__ import annotations

import json

from ecallisto_ng.core.calibration import Calibration, ChannelCal
from ecallisto_ng.core.units import UnitLevel


def build_calibration(coefficients_json: str, n_channels: int) -> Calibration:
    """Parse coefficient rows into a per-channel ``Calibration``.

    A single row is broadcast to all channels; otherwise the row count must
    equal ``n_channels``.
    """
    rows = json.loads(coefficients_json)
    if not rows:
        raise ValueError("calibration set has no coefficients")
    coeffs = [ChannelCal(a=r[0], b=r[1], cf=r[2], tb=r[3]) for r in rows]
    if len(coeffs) == 1:
        coeffs = coeffs * n_channels
    if len(coeffs) != n_channels:
        raise ValueError(
            f"calibration has {len(coeffs)} channels, need {n_channels}"
        )
    return Calibration(channels=tuple(coeffs))


def resolve(
    unit_str: str, coefficients_json: str | None, n_channels: int
) -> tuple[UnitLevel, Calibration | None]:
    """Resolve an instrument's (unit, calibration) for a recording.

    Raw unless a calibrated unit *and* coefficients are present (DESIGN 6b).
    """
    try:
        unit = UnitLevel(unit_str)
    except ValueError:
        unit = UnitLevel.RAW
    if unit is UnitLevel.RAW or not coefficients_json:
        return UnitLevel.RAW, None
    return unit, build_calibration(coefficients_json, n_channels)
