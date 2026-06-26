# SPDX-License-Identifier: AGPL-3.0-or-later
"""Callisto driver self-heal: stall/corrupt/error recover; dead -> Fatal."""

from __future__ import annotations

import itertools

import pytest

from ecallisto_ng.core import Channel, FatalInstrumentError
from ecallisto_ng.drivers.callisto import (
    CallistoConfig,
    CallistoDriver,
    SimulatedCallisto,
)


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
