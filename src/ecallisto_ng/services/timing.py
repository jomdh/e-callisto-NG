"""Time sources + per-class timestamping correction (DESIGN 12a / ADR-0009).

`SystemTimeSource` reads the OS clock + chrony offset/lock; `GpsTimeSource`
reads a GPS/PPS reference (thin, hardware-dependent); `FakeTimeSource` is for
tests. `corrected_timestamp` applies a documented per-instrument-class latency
correction so the recorded time reflects when the sky signal was sampled.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ecallisto_ng.core.units import InstrumentClass
from ecallisto_ng.services.clock import (
    clock_offset_ms,
    clock_synced,
)

# Per-class acquisition latency (ms): the delay between the sky signal and the
# host timestamp. Heterodyne adds serial + sweep latency; host-DSP SDR adds a
# buffer; FPGA SDR is near-zero. Documented constants, refined per deployment.
_LATENCY_MS: dict[str, float] = {
    InstrumentClass.HETERODYNE: 20.0,
    InstrumentClass.SDR_SOFT: 10.0,
    InstrumentClass.SDR_FPGA: 1.0,
}


class SystemTimeSource:
    name = "system"

    def now(self) -> datetime:
        return datetime.now(UTC)

    def offset_ms(self) -> float | None:
        return clock_offset_ms()

    def locked(self) -> bool:
        return clock_synced() is True


class GpsTimeSource:  # pragma: no cover - needs a GPS/PPS device
    """GPS/PPS reference via gpsd/chrony refclock (thin wrapper)."""

    name = "gps"

    def now(self) -> datetime:
        return datetime.now(UTC)

    def offset_ms(self) -> float | None:
        return clock_offset_ms()

    def locked(self) -> bool:
        return clock_synced() is True


class FakeTimeSource:
    """Deterministic time source for tests."""

    name = "fake"

    def __init__(
        self,
        at: datetime,
        offset_ms_value: float | None = 0.0,
        is_locked: bool = True,
    ) -> None:
        self._at = at
        self._offset = offset_ms_value
        self._locked = is_locked

    def now(self) -> datetime:
        return self._at

    def offset_ms(self) -> float | None:
        return self._offset

    def locked(self) -> bool:
        return self._locked


def get_time_source(name: str) -> SystemTimeSource | GpsTimeSource:
    """The configured active time source (``system`` or ``gps``)."""
    if name == "gps":
        return GpsTimeSource()
    return SystemTimeSource()


def corrected_timestamp(nominal: datetime, instrument_class: str) -> datetime:
    """Shift a nominal timestamp back by the class's acquisition latency."""
    latency = _LATENCY_MS.get(instrument_class, 0.0)
    return nominal - timedelta(milliseconds=latency)
