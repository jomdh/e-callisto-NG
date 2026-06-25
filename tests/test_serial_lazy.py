# SPDX-License-Identifier: AGPL-3.0-or-later
"""SerialConnection opens lazily; building a driver never touches hardware."""

from __future__ import annotations

from ecallisto_ng.connections.serial_link import SerialConnection
from ecallisto_ng.core.units import InstrumentClass
from ecallisto_ng.services.recorder import build_driver


def test_serial_connection_does_not_open_on_construction() -> None:
    # a bogus port would fail immediately if __init__ opened it
    conn = SerialConnection("/dev/does-not-exist-xyz")
    conn.close()  # no-op before any I/O -- nothing was opened


def test_build_heterodyne_driver_no_hardware() -> None:
    # building + reading capabilities must not open the serial port (this is
    # what the instrument detail page / capabilities endpoint do)
    driver = build_driver("heterodyne", "/dev/does-not-exist-xyz", 1, 200)
    caps = driver.capabilities  # static -> no hardware access
    assert caps.instrument_class is InstrumentClass.HETERODYNE
    from ecallisto_ng.core.contracts import BenchCapable

    assert isinstance(driver, BenchCapable)  # the page's gate, hardware-free
