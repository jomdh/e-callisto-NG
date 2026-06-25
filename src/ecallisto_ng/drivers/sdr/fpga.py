# SPDX-License-Identifier: AGPL-3.0-or-later
"""Class-3 SDR driver: the FPGA does the DSP.

The device streams ready power spectra; the host just ingests, frames, and
delivers them (DESIGN 5a). Reached over a network ``Connection`` (or USB). Wire
framing: each sweep is STX (0x02) followed by ``nchannels`` 8-bit power values.

An in-memory ``SimulatedFpga`` lets the whole stack run hardware-free.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime

from ecallisto_ng.core.connection import Connection
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

_STX = 0x02
_READ = 4096


class FpgaSdrDriver:
    """An SDR whose channelization runs on the device (FPGA)."""

    def __init__(
        self,
        connection: Connection,
        channels: int = 256,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._conn = connection
        self._n = channels
        self._clock = clock or (lambda: datetime.now(UTC))
        self._running = False
        self._rx = bytearray()
        self._sweep = 0

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            instrument_class=InstrumentClass.SDR_FPGA,
            processing_location=ProcessingLocation.DEVICE,
            link=LinkKind.NETWORK,
            bands_mhz=((45.0, 870.0),),
            max_channels=4096,
            bit_depth=8,
            max_sample_rate_hz=1000.0,
            supports_overview=True,
            supports_calibration=False,
        )

    def connect(self) -> None:
        self._conn.connect()  # type: ignore[attr-defined]

    def identify(self) -> InstrumentInfo:
        return InstrumentInfo(model="SDR-FPGA", firmware="fpga-1.0")

    def configure(
        self, channels: Sequence[Channel], sample_rate_hz: float
    ) -> None:
        if not channels:
            raise ValueError("at least one channel required")
        self._n = len(channels)

    def start(self) -> None:
        self._conn.write(b"START\n")
        self._running = True

    def stop(self) -> None:
        self._conn.write(b"STOP\n")
        self._running = False

    def stream(self) -> Iterator[SpectrumFrame]:
        while self._running:
            frame = self._read_frame()
            if frame is not None:
                yield frame

    def overview(self) -> Iterator[SpectrumFrame]:
        self._conn.write(b"START\n")
        self._running = True
        frame = self._read_frame()
        self._running = False
        if frame is not None:
            yield frame

    def close(self) -> None:
        self._running = False
        self._conn.close()

    def _read_frame(self) -> SpectrumFrame | None:
        # accumulate until STX + n payload bytes are available
        while True:
            stx = self._rx.find(bytes([_STX]))
            if stx >= 0 and len(self._rx) - stx - 1 >= self._n:
                payload = self._rx[stx + 1 : stx + 1 + self._n]
                del self._rx[: stx + 1 + self._n]
                self._sweep += 1
                return SpectrumFrame(
                    timestamp_utc=self._clock(),
                    monotonic_ns=self._sweep,
                    values=tuple(payload),
                    unit=UnitLevel.RAW,
                )
            chunk = self._conn.read(_READ)
            if not chunk:
                return None
            self._rx += chunk


class SimulatedFpga:
    """In-memory FPGA device: emits STX + nchannels power bytes per sweep."""

    def __init__(self, channels: int = 256, seed: int = 0) -> None:
        self._n = channels
        self._rng = random.Random(seed)
        self._out = bytearray()
        self._running = False
        self._sweep = 0

    def connect(self) -> None:
        pass

    def write(self, data: bytes) -> None:
        if b"START" in data:
            self._running = True
        if b"STOP" in data:
            self._running = False

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        if self._running and not self._out:
            self._emit_sweep()
        chunk = bytes(self._out[:size])
        del self._out[:size]
        return chunk

    def close(self) -> None:
        self._running = False

    def _emit_sweep(self) -> None:
        center = self._sweep % self._n
        width = max(self._n / 12.0, 1.0)
        self._out.append(_STX)
        for ch in range(self._n):
            dist = (ch - center) / width
            peak = 255.0 * pow(2.718281828, -0.5 * dist * dist)
            noise = self._rng.uniform(0, 20.0)
            self._out.append(int(min(255.0, peak + noise)))
        self._sweep += 1


def build_fpga_driver(address: str, channels: int) -> FpgaSdrDriver:
    """A network FPGA if ``host:port`` is given, else the simulator."""
    if ":" in address:
        from ecallisto_ng.connections.network import NetworkConnection

        host, port = address.rsplit(":", 1)
        conn: Connection = NetworkConnection(host, int(port))
    else:
        conn = SimulatedFpga(channels)
    return FpgaSdrDriver(conn, channels=channels)
