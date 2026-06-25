"""A finished block of spectra plus the metadata needed to persist it.

An :class:`ecallisto_ng.core.OutputWriter` turns a ``Recording`` into a science
product (e.g. FITS). Frames carry sample values and timestamps but not the
frequency axis or station identity, so those are bundled here. Kept as frozen
dataclasses so ``core`` stays dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass

from ecallisto_ng.core.calibration import Calibration
from ecallisto_ng.core.spectra import Channel, SpectrumFrame
from ecallisto_ng.core.units import UnitLevel


@dataclass(frozen=True)
class RecordingMeta:
    """Station/instrument context for a recording's header."""

    instrument: str
    origin: str = "e-CALLISTO NG"
    latitude_deg: float = 0.0  # +N / -S
    longitude_deg: float = 0.0  # +E / -W
    altitude_m: float = 0.0
    frqfile: str = ""
    pwm: int = 0  # tuner gain (PWM) value
    focus_code: int = 0
    # Timing provenance (DESIGN 12a / ADR-0009).
    time_source: str = "system"
    clock_offset_ms: float | None = None


@dataclass(frozen=True)
class Recording:
    """Spectra to be written, with their frequency axis and metadata.

    ``sample_rate_hz`` is the **sweep** rate (frames per second); the time-axis
    step is its reciprocal.
    """

    meta: RecordingMeta
    channels: tuple[Channel, ...]
    frames: tuple[SpectrumFrame, ...]
    sample_rate_hz: float
    unit: UnitLevel = UnitLevel.RAW
    calibration: Calibration | None = None
