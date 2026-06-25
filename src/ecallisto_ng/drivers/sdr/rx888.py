# SPDX-License-Identifier: AGPL-3.0-or-later
"""RX-888 MkII driver: a class-2 (host-DSP) SDR over USB3 (Cypress FX3).

The RX-888 MkII streams raw IQ over a Cypress FX3 USB3 link; the station's CPU
does the channelization (FFT) to produce normalized spectra -- the class-2 case
(DESIGN 5a). The DSP and the contract surface live here; the **IQ source** is a
seam with two implementations:

- ``SyntheticRx888Source`` -- a hardware-free generator so the whole pipeline
  (record -> FITS) runs anywhere, including CI and a Pi without the RX-888
  backend installed. Its firmware reports ``synthetic`` so the provenance is
  never ambiguous.
- ``_open_hardware_source`` -- the real seam: it lazily imports an RX-888
  streaming backend (the ``e-Callisto_Py_RX-888_MK_II`` tooling / ``librx888``)
  and raises a clear error if it is absent. This is where real FX3 streaming
  plugs in on the station; it is not exercised in CI (no hardware).

Selection: ``build_rx888_driver`` uses the hardware source when a backend is
importable, else the synthetic source -- and ``identify`` reports which, so an
operator can always see whether a recording is real or synthetic.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

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

logger = logging.getLogger(__name__)

# RX-888 MkII USB id (Cypress FX3). DFU/bootloader = 04b4:00f3.
RX888_USB_IDS = ("04b4:00f3", "04b4:00f1")


@runtime_checkable
class IqSource(Protocol):
    """A source of complex IQ blocks for host DSP."""

    @property
    def firmware(self) -> str:
        """Backend/firmware id (e.g. ``synthetic`` or a real version)."""

    def read_iq(self, n: int) -> np.ndarray:
        """Return ``n`` complex IQ samples."""

    def close(self) -> None:
        """Release the source."""


class SyntheticRx888Source:
    """Hardware-free IQ: a band-drifting tone + complex noise."""

    firmware = "synthetic"

    def __init__(self, seed: int = 0) -> None:
        self._rng = np.random.default_rng(seed)
        self._sweep = 0

    def read_iq(self, n: int) -> np.ndarray:
        t = np.arange(n)
        freq = (self._sweep % n) / n
        tone = np.exp(2j * np.pi * freq * t)
        noise = (
            self._rng.standard_normal(n) + 1j * self._rng.standard_normal(n)
        ) * 0.1
        self._sweep += 1
        return tone + noise

    def close(self) -> None:
        return None


def _open_hardware_source(
    address: str,
) -> IqSource:  # pragma: no cover - needs the RX-888 backend + hardware
    """Open the real RX-888 IQ stream, or raise if the backend is absent.

    On the station this imports the RX-888 streaming backend (the
    ``e-Callisto_Py_RX-888_MK_II`` tooling / ``librx888``) and opens the FX3
    device. Kept behind a lazy import so the suite has no hard dependency on
    a hardware-only library.
    """
    try:
        import rx888
    except ImportError as exc:
        raise RuntimeError(
            "RX-888 backend not installed; install the RX-888 streaming "
            "library on the station, or run the instrument in synthetic mode"
        ) from exc
    return rx888.open_stream(address)


def hardware_available() -> bool:
    """True if a real RX-888 streaming backend can be imported."""
    try:
        import rx888  # noqa: F401

        return True
    except ImportError:
        return False


class Rx888Driver:
    """RX-888 MkII: USB3 IQ in, host FFT out -> normalized 8-bit spectra."""

    def __init__(
        self,
        channels: int = 256,
        sample_rate_hz: float = 4.0,
        address: str = "",
        synthetic: bool | None = None,
        seed: int = 0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if channels < 2:
            raise ValueError("channels must be >= 2")
        self._n = channels
        self._rate = sample_rate_hz
        self._address = address
        # None -> auto: real backend if importable, else synthetic.
        self._synthetic = (
            (not hardware_available()) if synthetic is None else synthetic
        )
        self._seed = seed
        self._clock = clock or (lambda: datetime.now(UTC))
        self._source: IqSource | None = None
        self._running = False
        self._sweep = 0

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            instrument_class=InstrumentClass.SDR_SOFT,
            processing_location=ProcessingLocation.HOST,
            link=LinkKind.USB,
            # HF direct sampling + VHF/UHF via the R820T2 tuner.
            bands_mhz=((1.5, 30.0), (45.0, 870.0)),
            max_channels=8192,
            bit_depth=8,  # normalized product
            max_sample_rate_hz=1000.0,
            supports_overview=True,
            supports_calibration=False,
        )

    def connect(self) -> None:
        if self._synthetic:
            self._source = SyntheticRx888Source(self._seed)
            logger.warning(
                "RX-888 running in SYNTHETIC mode (no hardware backend)"
            )
        else:
            self._source = _open_hardware_source(self._address)

    def identify(self) -> InstrumentInfo:
        if self._source is None:
            raise RuntimeError("connect() before identify()")
        return InstrumentInfo(
            model="RX-888 MkII", firmware=self._source.firmware
        )

    def configure(
        self, channels: Sequence[Channel], sample_rate_hz: float
    ) -> None:
        if not channels:
            raise ValueError("at least one channel required")
        self._n = len(channels)
        self._rate = sample_rate_hz

    def start(self) -> None:
        if self._source is None:
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
        if self._source is not None:
            self._source.close()
            self._source = None

    def _dsp_frame(self) -> SpectrumFrame:
        """Host DSP: IQ block -> FFT -> normalized 8-bit power spectrum."""
        assert self._source is not None
        iq = self._source.read_iq(self._n)
        spectrum = np.abs(np.fft.fftshift(np.fft.fft(iq))) ** 2
        power = 10.0 * np.log10(spectrum + 1e-6)
        lo, hi = float(power.min()), float(power.max())
        scaled = (
            (power - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros(self._n)
        )
        self._sweep += 1
        return SpectrumFrame(
            timestamp_utc=self._clock(),
            monotonic_ns=self._sweep,
            values=tuple(int(v) for v in scaled.astype(np.uint8)),
            unit=UnitLevel.RAW,
        )


def build_rx888_driver(address: str, channels: int) -> Rx888Driver:
    """Construct an RX-888 driver (auto synthetic/hardware by backend)."""
    return Rx888Driver(channels=channels, address=address)


def is_rx888_address(address: str) -> bool:
    """True if an address points at an RX-888 (USB id or ``rx888`` marker)."""
    a = address.lower()
    return "rx888" in a or any(uid in a for uid in RX888_USB_IDS)
