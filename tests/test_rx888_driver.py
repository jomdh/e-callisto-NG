# SPDX-License-Identifier: AGPL-3.0-or-later
"""RX-888 MkII SDR driver: contract, synthetic DSP, routing (M31)."""

from __future__ import annotations

from datetime import UTC, datetime

from ecallisto_ng.core.contracts import InstrumentDriver
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.core.units import InstrumentClass, ProcessingLocation
from ecallisto_ng.drivers.sdr.rx888 import (
    Rx888Driver,
    SyntheticRx888Source,
    build_rx888_driver,
    is_rx888_address,
)
from ecallisto_ng.services.recorder import build_driver


def _driver() -> Rx888Driver:
    return Rx888Driver(channels=64, synthetic=True, seed=1)


def test_conforms_to_contract() -> None:
    assert isinstance(_driver(), InstrumentDriver)


def test_capabilities() -> None:
    caps = _driver().capabilities
    assert caps.instrument_class is InstrumentClass.SDR_SOFT
    assert caps.processing_location is ProcessingLocation.HOST
    assert caps.supports_overview is True
    # HF direct + VHF/UHF tuner bands
    assert (1.5, 30.0) in caps.bands_mhz
    assert (45.0, 870.0) in caps.bands_mhz


def test_synthetic_lifecycle_and_frames() -> None:
    d = _driver()
    d.connect()
    info = d.identify()
    assert info.model == "RX-888 MkII"
    assert info.firmware == "synthetic"  # provenance: not real hardware
    d.configure([Channel(frequency_mhz=45.0 + i) for i in range(64)], 4.0)
    d.start()
    frames = list(d.stream(frames=5))
    d.stop()
    d.close()
    assert len(frames) == 5
    for f in frames:
        assert len(f.values) == 64
        assert all(0 <= v <= 255 for v in f.values)  # normalized 8-bit


def test_overview_one_shot() -> None:
    d = _driver()
    d.connect()
    frames = list(d.overview())
    assert len(frames) == 1


def test_synthetic_source_iq_shape() -> None:
    src = SyntheticRx888Source(seed=2)
    iq = src.read_iq(128)
    assert iq.shape == (128,)
    assert iq.dtype.kind == "c"  # complex


def test_address_detection() -> None:
    assert is_rx888_address("usb:04b4:00f3") is True
    assert is_rx888_address("rx888") is True
    assert is_rx888_address("/dev/ttyUSB0") is False
    assert is_rx888_address("usb:0bda:2838") is False  # RTL-SDR, not RX-888


def test_build_driver_routes_rx888() -> None:
    # an sdr_soft instrument with an RX-888 USB address -> the RX-888 driver
    d = build_driver("sdr_soft", "usb:04b4:00f3", 1, 128)
    assert isinstance(d, Rx888Driver)
    # a plain sdr_soft -> the generic soft driver, not RX-888
    other = build_driver("sdr_soft", "", 1, 128)
    assert not isinstance(other, Rx888Driver)


def test_clock_injection() -> None:
    fixed = datetime(2026, 6, 25, 12, 0, 0, tzinfo=UTC)
    d = build_rx888_driver("usb:04b4:00f3", 32)
    d2 = Rx888Driver(channels=32, synthetic=True, clock=lambda: fixed)
    d2.connect()
    f = next(d2.overview())
    assert f.timestamp_utc == fixed
    assert isinstance(d, Rx888Driver)
