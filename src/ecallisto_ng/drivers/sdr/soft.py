# SPDX-License-Identifier: AGPL-3.0-or-later
"""Class-2 SDR driver: the host does the DSP.

Synthesizes IQ samples (a drifting tone + noise) and turns them into power
spectra on the host via FFT -- the class-2 case where the device only streams
raw IQ and the station's CPU produces the spectrogram (DESIGN 5a). With real
hardware the IQ source would be a SoapySDR/librtlsdr stream; here it is
synthetic so the whole stack runs hardware-free.

This is a *plugin*: it implements the InstrumentDriver contract and delivers
the same normalized 8-bit spectra as the heterodyne driver, so nothing
downstream changes.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime

import numpy as np

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


class SoftSdrDriver:
    """An SDR whose channelization runs in host software (FFT)."""

    def __init__(
        self,
        channels: int = 256,
        sample_rate_hz: float = 4.0,
        seed: int = 0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if channels < 2:
            raise ValueError("channels must be >= 2")
        self._n = channels
        self._rate = sample_rate_hz
        self._rng = np.random.default_rng(seed)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._connected = False
        self._running = False
        self._sweep = 0

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            instrument_class=InstrumentClass.SDR_SOFT,
            processing_location=ProcessingLocation.HOST,
            link=LinkKind.USB,
            bands_mhz=((45.0, 870.0),),
            max_channels=4096,
            bit_depth=8,  # normalized product
            max_sample_rate_hz=1000.0,
            supports_overview=True,
            supports_calibration=False,
        )

    def connect(self) -> None:
        self._connected = True

    def identify(self) -> InstrumentInfo:
        if not self._connected:
            raise RuntimeError("connect() before identify()")
        return InstrumentInfo(model="SDR-SOFT", firmware="dsp-1.0")

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
        if not self._running:
            raise RuntimeError("start() before stream()")
        emitted = 0
        while self._running and (frames is None or emitted < frames):
            yield self._dsp_frame()
            emitted += 1

    def overview(self) -> Iterator[SpectrumFrame]:
        yield self._dsp_frame()

    def close(self) -> None:
        self._running = False
        self._connected = False

    def _dsp_frame(self) -> SpectrumFrame:
        """Host DSP: synth IQ -> FFT -> normalized 8-bit power spectrum."""
        n = self._n
        t = np.arange(n)
        # a tone that drifts across the band, plus complex noise
        bin_idx = self._sweep % n
        freq = bin_idx / n
        tone = np.exp(2j * math.pi * freq * t)
        noise = (
            self._rng.standard_normal(n) + 1j * self._rng.standard_normal(n)
        ) * 0.1
        spectrum = np.abs(np.fft.fftshift(np.fft.fft(tone + noise))) ** 2
        power = 10.0 * np.log10(spectrum + 1e-6)
        lo, hi = power.min(), power.max()
        scaled = (power - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros(n)
        values = scaled.astype(np.uint8)
        self._sweep += 1
        return SpectrumFrame(
            timestamp_utc=self._clock(),
            monotonic_ns=self._sweep,
            values=tuple(int(v) for v in values),
            unit=UnitLevel.RAW,
        )
