"""Normalized spectra and capability value types.

The **driver boundary sits at "normalized spectra"** (DESIGN 5a): every
instrument driver, whatever its class, hands the rest of the suite the same
product -- a stream of timestamped spectra plus a capabilities descriptor.
Nothing class-specific (serial/EEPROM, host DSP, FPGA ingest) appears here.

These are plain frozen dataclasses on purpose: ``core`` stays dependency-free
(no pydantic, no numpy), so any layer can import it without pulling in a stack.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from ecallisto_ng.core.units import (
    InstrumentClass,
    LinkKind,
    ProcessingLocation,
    UnitLevel,
)


@dataclass(frozen=True)
class Channel:
    """One frequency channel in a sweep."""

    frequency_mhz: float
    light_curve: bool = False  # flagged for light-curve extraction


@dataclass(frozen=True)
class Capabilities:
    """What a driver can do -- the suite adapts to this, not to a class.

    Feature-detection, not hard-coding: schedulers, writers and the UI read
    these fields rather than branching on instrument type (DESIGN 5a).
    """

    instrument_class: InstrumentClass
    processing_location: ProcessingLocation
    link: LinkKind
    bands_mhz: tuple[tuple[float, float], ...]  # supported (low, high) bands
    max_channels: int
    bit_depth: int  # SDR >> 8; writers must not assume 8-bit (DESIGN 6a)
    max_sample_rate_hz: float
    supports_overview: bool = False
    supports_calibration: bool = False


@dataclass(frozen=True)
class InstrumentInfo:
    """Identity reported by a connected instrument."""

    model: str
    firmware: str
    serial: str | None = None


@dataclass(frozen=True)
class SpectrumFrame:
    """One normalized spectrum: a single sweep across the channels.

    ``values`` are native ADC samples (length == number of channels), at the
    instrument's bit depth, and ``unit`` is ``RAW`` unless an explicit
    calibration was applied upstream of the driver boundary.
    """

    timestamp_utc: datetime  # UTC time the sweep was acquired
    monotonic_ns: int  # monotonic clock for precise spacing / ordering
    values: Sequence[int]
    unit: UnitLevel = UnitLevel.RAW
    focus_code: int = 0


@dataclass(frozen=True)
class Housekeeping:
    """Non-science telemetry published alongside frames (voltages, state)."""

    timestamp_utc: datetime
    readings: dict[str, float] = field(default_factory=dict)
    state: str = "unknown"
