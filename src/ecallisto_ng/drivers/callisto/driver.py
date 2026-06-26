# SPDX-License-Identifier: AGPL-3.0-or-later
"""CallistoDriver -- the class-1 heterodyne instrument driver.

Implements :class:`ecallisto_ng.core.InstrumentDriver` over a
:class:`ecallisto_ng.core.connection.Connection`, using the pure protocol
helpers and the stream parser. It owns the legacy lifecycle: reset -> identify
-> detect firmware -> upload channels -> init -> start -> stream -> stop.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from ecallisto_ng.core.connection import Connection
from ecallisto_ng.core.errors import (
    FatalInstrumentError,
    RecoverableInstrumentError,
)
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

# Self-heal (ADR-0010 / M34): a stalled or corrupt stream triggers an in-driver
# reset->init->start; too many resets in a window escalates to Fatal.
_RESET_WINDOW_S = 60.0
_RESET_BUDGET = 3
# Stall = no data for max(_MIN_NO_DATA_S, _STALL_SWEEPS / sweep_rate).
_MIN_NO_DATA_S = 3.0
_STALL_SWEEPS = 5.0

_log = logging.getLogger(__name__)


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
        # Stall timeout knobs (overridable in tests for speed).
        self._min_no_data_s = _MIN_NO_DATA_S
        self._stall_sweeps = _STALL_SWEEPS

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
        # Unrecognized devices fall back to the default profile (10-bit,
        # 27 MHz) like the legacy code, not rejected (audit A5).
        self._firmware = p.detect_firmware(status)
        return InstrumentInfo(
            model="Callisto", firmware=self._firmware.version
        )

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
        self._running = False
        try:
            self._conn.write(p.STOP)
        except OSError:
            pass  # best-effort: the device may already be gone

    def stream(self) -> Iterator[SpectrumFrame]:
        """Yield sweeps, self-healing transient stalls/corruption.

        Bounded liveness (ADR-0010): never blocks indefinitely. A no-data
        stall, a serial error, or a corrupt sweep triggers an in-driver
        reset->init->start; exceeding the reset budget raises
        ``FatalInstrumentError`` for the engine to rebuild + re-arm.
        """
        parser = StreamParser(self._nchannels, self._firmware.data10bit)
        # Timeout on FRAMES produced, not bytes read: a device that streams
        # unparseable junk (mid-frame desync after an abrupt kill) keeps the
        # read non-empty forever, so a bytes-based stall never fires and the
        # recording wedges with zero frames. Tracking last-frame catches both
        # silence AND data-without-sweeps.
        last_frame = time.monotonic()
        resets: deque[float] = deque()
        while self._running:
            try:
                chunk = self._read_chunk()
            except OSError as exc:
                parser = self._recover(resets, f"serial error: {exc}")
                last_frame = time.monotonic()
                continue
            if chunk:
                try:
                    items = list(parser.feed(chunk))
                except RecoverableInstrumentError as exc:
                    parser = self._recover(resets, str(exc))
                    last_frame = time.monotonic()
                    continue
                for item in items:
                    if isinstance(item, ParsedSweep):
                        last_frame = time.monotonic()
                        yield self._frame(item.values)
                    elif isinstance(item, ParsedMessage):
                        if "Stopped" in item.text:
                            self._running = False
            if (
                self._running
                and time.monotonic() - last_frame > self._no_data_timeout()
            ):
                parser = self._recover(resets, "no frames (stall)")
                last_frame = time.monotonic()

    def _no_data_timeout(self) -> float:
        rate = max(self._sweeps_per_second, 0.1)
        return max(self._min_no_data_s, self._stall_sweeps / rate)

    def _recover(self, resets: deque[float], reason: str) -> StreamParser:
        """Soft reset->init->start, or escalate to Fatal past the budget."""
        now = time.monotonic()
        while resets and now - resets[0] > _RESET_WINDOW_S:
            resets.popleft()
        if len(resets) >= _RESET_BUDGET:
            self._running = False
            raise FatalInstrumentError(
                f"unrecoverable after {len(resets)} resets in "
                f"{int(_RESET_WINDOW_S)}s ({reason})"
            )
        resets.append(now)
        _log.warning("callisto self-heal: soft reset (%s)", reason)
        try:
            self._soft_reset()
        except OSError:
            pass  # the reset itself failed; the next read re-enters recovery
        return StreamParser(self._nchannels, self._firmware.data10bit)

    def _soft_reset(self) -> None:
        """Re-arm acquisition without re-writing the EEPROM channel table.

        Legacy reset->init->start: channels persist in EEPROM, so only the
        clock/gain init and the start sequence are resent.
        """
        self._conn.write(p.RESET)
        self._drain()
        pixels = max(int(round(self._sweeps_per_second * self._nchannels)), 1)
        for cmd in p.init_commands(
            self._cfg.clocksource,
            pixels,
            self._cfg.agclevel,
            self._cfg.chargepump,
        ):
            self._conn.write(cmd)
        self._conn.write(
            p.start_commands(self._cfg.focuscode, self._nchannels)
        )

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
        try:
            self._conn.write(p.HALT)
        except OSError:
            pass  # best-effort: the device may already be gone
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
