"""CallistoDriver against the in-memory simulator -- end-to-end."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime

from ecallisto_ng.core import (
    Channel,
    InstrumentDriver,
    SpectrumFrame,
    UnitLevel,
)
from ecallisto_ng.drivers.callisto import (
    CallistoConfig,
    CallistoDriver,
    SimulatedCallisto,
)
from ecallisto_ng.drivers.callisto.parser import (
    ParsedMessage,
    ParsedSweep,
    StreamParser,
)


def _fixed_clock() -> datetime:
    return datetime(2026, 6, 25, 10, 0, 0, tzinfo=UTC)


def _driver(firmware: str = "1.8") -> CallistoDriver:
    sim = SimulatedCallisto(firmware=firmware)
    return CallistoDriver(
        sim, config=CallistoConfig(focuscode=1), clock=_fixed_clock
    )


def test_driver_conforms_to_contract() -> None:
    assert isinstance(_driver(), InstrumentDriver)


def test_identify_detects_firmware() -> None:
    for fw in ("1.5", "1.7", "1.8"):
        driver = _driver(fw)
        driver.connect()
        info = driver.identify()
        assert info.model == "Callisto"
        assert info.firmware == fw


def test_record_end_to_end() -> None:
    channels = [Channel(frequency_mhz=45.0 + i) for i in range(32)]
    driver = _driver("1.8")
    driver.connect()
    driver.identify()
    driver.configure(channels, sample_rate_hz=4.0)
    driver.start()

    frames = list(itertools.islice(driver.stream(), 5))
    driver.stop()
    driver.close()

    assert len(frames) == 5
    for frame in frames:
        assert isinstance(frame, SpectrumFrame)
        assert frame.unit is UnitLevel.RAW
        assert len(frame.values) == 32
        assert all(0 <= v <= 255 for v in frame.values)  # normalized to 8-bit
        assert frame.timestamp_utc == _fixed_clock()


def test_overview_collects_a_wide_frame() -> None:
    driver = _driver("1.8")
    driver.connect()
    driver.identify()
    frames = list(driver.overview())
    assert len(frames) == 1
    assert len(frames[0].values) == 8  # the simulator emits 8 overview points


# -- StreamParser unit tests ----------------------------------------------


def test_parser_splits_messages_and_sweeps() -> None:
    parser = StreamParser(nchannels=2, data10bit=False)
    # a message, then DATA_START ('2') + two 4-hex samples (one sweep), then
    # another -- the leading '2' marks data; subsequent '2's are hex digits
    stream = b"$CRX:Started\r2" + b"000A" + b"00FF" + b"0010" + b"0020"
    items = list(parser.feed(stream))
    messages = [i for i in items if isinstance(i, ParsedMessage)]
    sweeps = [i for i in items if isinstance(i, ParsedSweep)]
    assert messages[0].text == "CRX:Started"
    assert sweeps[0].values == [0x0A, 0xFF]
    assert sweeps[1].values == [0x10, 0x20]


def test_parser_skips_end_marker() -> None:
    parser = StreamParser(nchannels=2, data10bit=False)
    # END_MARKER (2323) must not count as a sample (the leading '2' is the
    # DATA_START; the '2323' that follows is read as a hex sample = 0x2323)
    items = list(parser.feed(b"2" + b"0005" + b"2323" + b"0007"))
    sweeps = [i for i in items if isinstance(i, ParsedSweep)]
    assert sweeps == [ParsedSweep([0x05, 0x07])]
