# SPDX-License-Identifier: AGPL-3.0-or-later
"""Callisto driver self-heal: stall/corrupt/error recover; dead -> Fatal."""

from __future__ import annotations

import itertools
import time
from pathlib import Path

import pytest

from ecallisto_ng.core import Channel, FatalInstrumentError, RecordingMeta
from ecallisto_ng.core.errors import RecoverableInstrumentError
from ecallisto_ng.drivers.callisto import (
    CallistoConfig,
    CallistoDriver,
    SimulatedCallisto,
)
from ecallisto_ng.services.acquisition import record_continuous
from ecallisto_ng.writers.fits import StandardFitsWriter


class _MuteConn:
    """A device that enumerates and accepts writes but never replies --
    the mute-at-startup case that used to park the handshake forever."""

    def __init__(self) -> None:
        self.closed = False

    def write(self, data: bytes) -> None:
        pass

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        return b""

    def close(self) -> None:
        self.closed = True


def _driver(sim: SimulatedCallisto) -> CallistoDriver:
    d = CallistoDriver(sim, config=CallistoConfig(focuscode=1))
    d.connect()
    d.identify()
    d.configure([Channel(frequency_mhz=45.0 + i) for i in range(8)], 4.0)
    d.start()
    d._min_no_data_s = 0.02  # fast stall detection for the test
    d._stall_sweeps = 0.02
    return d


def test_stall_recovers() -> None:
    sim = SimulatedCallisto("1.8")
    d = _driver(sim)
    stream = d.stream()
    assert len(next(stream).values) == 8  # streaming
    sim.stall()  # go silent (recoverable)
    assert len(next(stream).values) == 8  # soft reset -> resumed
    d.stop()


def test_corrupt_sweep_recovers() -> None:
    sim = SimulatedCallisto("1.8")
    d = _driver(sim)
    stream = d.stream()
    next(stream)
    sim.inject_corruption()  # one out-of-range sample -> parser raises
    assert len(next(stream).values) == 8  # soft reset -> resumed
    d.stop()


def test_serial_error_recovers() -> None:
    sim = SimulatedCallisto("1.8")
    d = _driver(sim)
    stream = d.stream()
    next(stream)
    sim.inject_read_error(1)  # one OSError on read
    assert len(next(stream).values) == 8  # soft reset -> resumed
    d.stop()


def test_second_recovery_reopens_the_port() -> None:
    # The first stall in the window is a cheap soft reset (no port reopen); a
    # second escalates to closing+reopening the OS fd -- the rung that actually
    # clears a mute/IO-errored port, as a process restart did (ADR-0012).
    class _SpyConn(SimulatedCallisto):
        def __init__(self, firmware: str = "1.8") -> None:
            super().__init__(firmware)
            self.close_calls = 0

        def close(self) -> None:
            self.close_calls += 1
            super().close()

    sim = _SpyConn("1.8")
    d = _driver(sim)
    stream = d.stream()
    next(stream)
    sim.stall()
    next(stream)  # 1st recovery: soft reset, no reopen
    assert sim.close_calls == 0
    sim.stall()
    next(stream)  # 2nd recovery: escalate to port reopen
    assert sim.close_calls == 1
    d.stop()


def test_identify_times_out_on_mute_device() -> None:
    # the alive-gate: a mute device fails identify() fast (a typed recoverable
    # fault), instead of blocking ~200s reading $CRX:Stopped (ADR-0010 M38).
    d = CallistoDriver(_MuteConn(), config=CallistoConfig())
    d._handshake_timeout_s = 0.05
    t0 = time.monotonic()
    with pytest.raises(RecoverableInstrumentError):
        d.identify()
    assert time.monotonic() - t0 < 1.0  # bounded, not ~200s


def test_configure_times_out_on_mute_device() -> None:
    d = CallistoDriver(_MuteConn(), config=CallistoConfig())
    d._handshake_timeout_s = 0.05
    with pytest.raises(RecoverableInstrumentError):
        d.configure([Channel(frequency_mhz=45.0)], 4.0)


def test_handshake_failure_releases_the_port(tmp_path: Path) -> None:
    # the whole point: a bounded handshake failure still runs the finally, so
    # the port is closed and the scheduler's next rebuild doesn't collide with
    # a leaked fd ("multiple access on port").
    conn = _MuteConn()
    d = CallistoDriver(conn, config=CallistoConfig())
    d._handshake_timeout_s = 0.02
    with pytest.raises(RecoverableInstrumentError):
        record_continuous(
            d,
            StandardFitsWriter(),
            [Channel(frequency_mhz=45.0 + i) for i in range(4)],
            RecordingMeta(instrument="MUTE", focus_code=1),
            tmp_path,
            sweeps_per_second=4.0,
            frames_per_file=10,
        )
    assert conn.closed  # finally ran -> port released for the next rebuild


def test_dead_device_escalates_to_fatal() -> None:
    sim = SimulatedCallisto("1.8")
    d = _driver(sim)
    stream = d.stream()
    next(stream)
    sim.make_dead()  # ignores restart commands -> unrecoverable
    with pytest.raises(FatalInstrumentError):
        # drains the reset budget, then escalates -- never hangs
        list(itertools.islice(stream, 100))


def test_garbage_stream_recovers() -> None:
    # data arrives but never forms a sweep -> the no-FRAME timeout must fire
    # (a bytes-based stall never would), soft reset, and resume.
    sim = SimulatedCallisto("1.8")
    d = _driver(sim)
    stream = d.stream()
    assert len(next(stream).values) == 8
    sim.emit_noise()  # device streams junk, no sweeps
    assert len(next(stream).values) == 8  # recovered
    d.stop()
