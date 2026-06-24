"""M0 seam tests: the fake driver must satisfy the InstrumentDriver contract.

These verify the *seam*, not the Callisto hardware: any driver that conforms
to the contract can be driven the same way. They also serve as the executable
spec for what a real driver must provide.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ecallisto_ng.core import (
    Capabilities,
    InstrumentDriver,
    SpectrumFrame,
    UnitLevel,
)
from ecallisto_ng.drivers.fake import FakeDriver


def _fixed_clock() -> datetime:
    return datetime(2026, 6, 24, 12, 0, 0, tzinfo=UTC)


def test_fake_driver_conforms_to_contract() -> None:
    driver = FakeDriver()
    assert isinstance(driver, InstrumentDriver)


def test_capabilities_are_sane() -> None:
    caps = FakeDriver().capabilities
    assert isinstance(caps, Capabilities)
    assert caps.bit_depth == 8
    assert caps.max_channels >= 1
    assert caps.bands_mhz  # at least one band


def test_lifecycle_and_stream_shape() -> None:
    driver = FakeDriver(channels=32, clock=_fixed_clock)
    driver.connect()
    info = driver.identify()
    assert info.model == "FAKE"
    driver.start()

    frames = list(driver.stream(frames=10))
    driver.stop()
    driver.close()

    assert len(frames) == 10
    for frame in frames:
        assert isinstance(frame, SpectrumFrame)
        assert frame.unit is UnitLevel.RAW  # raw is always the default
        assert len(frame.values) == 32
        assert all(0 <= v <= 255 for v in frame.values)


def test_peak_drifts_across_channels() -> None:
    """Sanity: the synthetic peak moves, so it is not a constant frame."""
    driver = FakeDriver(channels=32, seed=1)
    driver.connect()
    driver.start()
    frames = list(driver.stream(frames=4))
    argmaxes = [
        max(range(len(f.values)), key=lambda i: f.values[i]) for f in frames
    ]
    assert len(set(argmaxes)) > 1


def test_stream_requires_start() -> None:
    driver = FakeDriver()
    driver.connect()
    try:
        next(driver.stream(frames=1))
    except RuntimeError:
        return
    raise AssertionError("stream() before start() should raise")
