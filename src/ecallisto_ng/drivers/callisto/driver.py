# SPDX-License-Identifier: AGPL-3.0-or-later
"""CallistoDriver -- the class-1 heterodyne instrument driver.

Implements :class:`ecallisto_ng.core.InstrumentDriver` over a
:class:`ecallisto_ng.core.connection.Connection`, using the pure protocol
helpers and the stream parser. It owns the legacy lifecycle: reset -> identify
-> detect firmware -> upload channels -> init -> start -> stream -> stop.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
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
from ecallisto_ng.drivers.callisto import protocol as p
from ecallisto_ng.drivers.callisto.parser import (
    ParsedMessage,
    ParsedSweep,
    StreamParser,
)

_READ_CHUNK = 4096
_MAX_EMPTY_READS = 200  # guards line/ack reads against a dead port


@dataclass
class CallistoConfig:
    """Static per-instrument settings not derived from the frequency plan."""

    focuscode: int = 1
    agclevel: int = 120
    chargepump: bool = True
    clocksource: int = 1  # 1 = internal quartz, 2 = external 1 MHz, 0 = sw
    local_oscillator: float = 0.0


class CallistoDriver:
    """Drives one Callisto receiver and yields normalized 8-bit spectra."""

    def __init__(
        self,
        connection: Connection,
        config: CallistoConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._conn = connection
        self._cfg = config or CallistoConfig()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._firmware = p.FIRMWARE_15
        self._nchannels = 0
        self._sweeps_per_second = 1.0
        self._running = False
        self._rx = bytearray()

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            instrument_class=InstrumentClass.HETERODYNE,
            processing_location=ProcessingLocation.HOST,
            link=LinkKind.SERIAL,
            bands_mhz=((45.0, 870.0),),
            max_channels=512,
            bit_depth=8,  # delivered product is normalized to 8-bit
            max_sample_rate_hz=1000.0,
            supports_overview=True,
            supports_calibration=False,
        )

    # -- lifecycle ---------------------------------------------------------

    def connect(self) -> None:
        self._conn.write(p.RESET)
        self._drain()

    def identify(self) -> InstrumentInfo:
        self._conn.write(p.ID_QUERY)
        line = self._read_line()
        if line + "\r" != p.ID_RESPONSE.decode("ascii"):
            raise RuntimeError(f"not a Callisto (ID failed): {line!r}")
        self._conn.write(p.STATUS_QUERY)
        status = self._read_line()
        firmware = p.detect_firmware(status)
        if firmware is None:
            raise RuntimeError(f"unsupported firmware: {status!r}")
        self._firmware = firmware
        return InstrumentInfo(model="Callisto", firmware=firmware.version)

    def configure(
        self, channels: Sequence[Channel], sample_rate_hz: float
    ) -> None:
        """Program channels and rate. ``sample_rate_hz`` = sweeps per second.

        The receiver's clock counts *pixels* (samples) per second, so the
        divider is set from sweeps x channels (B1).
        """
        if not channels:
            raise ValueError("at least one channel required")
        self._nchannels = len(channels)
        self._sweeps_per_second = sample_rate_hz
        pixels_per_second = max(
            int(round(sample_rate_hz * self._nchannels)), 1
        )
        for index, channel in enumerate(channels):
            self._conn.write(
                p.channel_command(
                    index,
                    channel.frequency_mhz,
                    self._firmware,
                    local_oscillator=self._cfg.local_oscillator,
                    chargepump=self._cfg.chargepump,
                )
            )
            self._wait_for(p.EEPROM_READY)
        for cmd in p.init_commands(
            self._cfg.clocksource,
            pixels_per_second,
            self._cfg.agclevel,
            self._cfg.chargepump,
        ):
            self._conn.write(cmd)

    def start(self) -> None:
        if self._nchannels < 1:
            raise RuntimeError("configure() before start()")
        self._conn.write(
            p.start_commands(self._cfg.focuscode, self._nchannels)
        )
        self._running = True

    def stop(self) -> None:
        self._conn.write(p.STOP)
        self._running = False

    def stream(self) -> Iterator[SpectrumFrame]:
        parser = StreamParser(self._nchannels, self._firmware.data10bit)
        while self._running:
            chunk = self._read_chunk()
            if not chunk:
                continue
            for item in parser.feed(chunk):
                if isinstance(item, ParsedSweep):
                    yield self._frame(item.values)
                elif isinstance(item, ParsedMessage):
                    if "Stopped" in item.text:
                        self._running = False

    def overview(self) -> Iterator[SpectrumFrame]:
        self._conn.write(p.OVERVIEW)
        values: list[int] = []
        parser = StreamParser(1, self._firmware.data10bit)
        empties = 0
        while empties < _MAX_EMPTY_READS:
            chunk = self._read_chunk()
            if not chunk:
                empties += 1
                continue
            empties = 0
            for item in parser.feed(chunk):
                if isinstance(item, ParsedMessage):
                    freq, amp, done = _parse_overview_line(item.text)
                    if amp is not None:
                        values.append(amp)
                    if done:
                        yield self._frame(values)
                        return

    def close(self) -> None:
        self._running = False
        self._conn.write(p.HALT)
        self._conn.close()

    # -- BenchCapable (ADR-0005) ------------------------------------------

    def tune(self, frequency_mhz: float) -> None:
        self._conn.write(p.tune_command(frequency_mhz))

    def set_gain(self, pwm: int) -> None:
        self._conn.write(p.gain_command(pwm))

    def read_detector(self) -> float:
        self._conn.write(p.DETECTOR_QUERY)
        empties = 0
        while empties < _MAX_EMPTY_READS:
            chunk = self._read_chunk()
            if not chunk:
                empties += 1
                continue
            empties = 0
            mv = p.parse_detector(chunk.decode("ascii", "ignore"))
            if mv is not None:
                return mv
        return 0.0

    def set_relay(self, code: int) -> None:
        self._conn.write(p.relay_command(code))

    # -- helpers -----------------------------------------------------------

    def _frame(self, values: list[int]) -> SpectrumFrame:
        return SpectrumFrame(
            timestamp_utc=self._clock(),
            monotonic_ns=time.monotonic_ns(),
            values=tuple(values),
            unit=UnitLevel.RAW,
            focus_code=self._cfg.focuscode,
        )

    def _fill(self) -> int:
        data = self._conn.read(_READ_CHUNK)
        self._rx += data
        return len(data)

    def _read_chunk(self) -> bytes:
        self._fill()
        chunk = bytes(self._rx)
        self._rx = bytearray()
        return chunk

    def _drain(self) -> None:
        while self._fill():
            self._rx = bytearray()

    def _read_line(self) -> str:
        empties = 0
        while empties < _MAX_EMPTY_READS:
            idx = self._rx.find(b"\r")
            if idx >= 0:
                line = self._rx[:idx]
                del self._rx[: idx + 1]
                return line.decode("ascii", "replace")
            if self._fill() == 0:
                empties += 1
        raise TimeoutError("no line received from device")

    def _wait_for(self, marker: bytes) -> None:
        empties = 0
        while empties < _MAX_EMPTY_READS:
            idx = self._rx.find(marker)
            if idx >= 0:
                del self._rx[: idx + 1]
                return
            if self._fill() == 0:
                empties += 1
        raise TimeoutError(f"marker {marker!r} not received")


def _parse_overview_line(text: str) -> tuple[float, int | None, bool]:
    """Parse ``CRX:<freq>,<amp>`` overview rows. Returns (freq, amp, done)."""
    if not text.startswith("CRX:"):
        return 0.0, None, False
    body = text[len("CRX:") :]
    parts = body.split(",")
    if len(parts) != 2:
        return 0.0, None, False
    try:
        freq = float(parts[0])
        amp = int(parts[1])
    except ValueError:
        return 0.0, None, False
    return freq, amp, freq >= 869.999
