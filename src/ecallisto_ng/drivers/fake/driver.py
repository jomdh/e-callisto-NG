"""A synthetic instrument that needs no hardware.

``FakeDriver`` implements the :class:`~ecallisto_ng.core.InstrumentDriver`
contract and emits a believable spectrogram (a drifting spectral peak plus
noise). It lets the whole acquisition stack run in development and CI with no
receiver attached -- the "serial simulator" prerequisite from DESIGN M0.

Timing is injectable so tests are deterministic.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime

from ecallisto_ng.core.spectra import (
    Capabilities,
    Channel,
    InstrumentInfo,
    SpectrumFrame,
)
from ecallisto_ng.core.units import (
    InstrumentClass,
    LinkKind,
    ProcessingLocation,
    UnitLevel,
)

_DEFAULT_BANDS: tuple[tuple[float, float], ...] = ((45.0, 870.0),)


class FakeDriver:
    """An in-memory instrument emitting synthetic 8-bit spectra."""

    def __init__(
        self,
        channels: int = 64,
        sample_rate_hz: float = 4.0,
        bit_depth: int = 8,
        seed: int = 0,
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], int] | None = None,
    ) -> None:
        if channels < 1:
            raise ValueError("channels must be >= 1")
        self._n = channels
        self._rate = sample_rate_hz
        self._bit_depth = bit_depth
        self._max_value = (1 << bit_depth) - 1
        self._rng = random.Random(seed)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._monotonic = monotonic or time.monotonic_ns
        self._connected = False
        self._running = False
        self._focus_code = 0
        self._sweep = 0

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            instrument_class=InstrumentClass.HETERODYNE,
            processing_location=ProcessingLocation.HOST,
            link=LinkKind.SERIAL,
            bands_mhz=_DEFAULT_BANDS,
            max_channels=512,
            bit_depth=self._bit_depth,
            max_sample_rate_hz=1000.0,
            supports_overview=True,
            supports_calibration=False,
        )

    def connect(self) -> None:
        self._connected = True

    def identify(self) -> InstrumentInfo:
        if not self._connected:
            raise RuntimeError("connect() before identify()")
        return InstrumentInfo(model="FAKE", firmware="sim-1.0", serial="FAKE0")

    def configure(
        self, channels: Sequence[Channel], sample_rate_hz: float
    ) -> None:
        if not channels:
            raise ValueError("at least one channel required")
        self._n = len(channels)
        self._rate = sample_rate_hz

    def start(self) -> None:
        if not self._connected:
            raise RuntimeError("connect() before start()")
        self._running = True

    def stop(self) -> None:
        self._running = False

    def stream(self, frames: int | None = None) -> Iterator[SpectrumFrame]:
        """Yield synthetic frames until ``stop()`` or ``frames`` reached.

        ``frames=None`` streams indefinitely; pass an int in tests.
        """
        if not self._running:
            raise RuntimeError("start() before stream()")
        emitted = 0
        while self._running and (frames is None or emitted < frames):
            yield self._make_frame()
            emitted += 1

    def overview(self) -> Iterator[SpectrumFrame]:
        # A one-shot wide sweep; for the fake it is just a single frame.
        yield self._make_frame()

    def close(self) -> None:
        self._running = False
        self._connected = False

    def _make_frame(self) -> SpectrumFrame:
        """One sweep: a Gaussian peak drifting across channels, plus noise."""
        center = self._sweep % self._n
        width = max(self._n / 12.0, 1.0)
        values: list[int] = []
        for ch in range(self._n):
            dist = (ch - center) / width
            peak = self._max_value * pow(2.718281828, -0.5 * dist * dist)
            noise = self._rng.uniform(0, self._max_value * 0.08)
            v = int(min(self._max_value, peak + noise))
            values.append(v)
        self._sweep += 1
        return SpectrumFrame(
            timestamp_utc=self._clock(),
            monotonic_ns=self._monotonic(),
            values=tuple(values),
            unit=UnitLevel.RAW,
            focus_code=self._focus_code,
        )
