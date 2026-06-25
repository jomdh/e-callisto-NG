"""Data-loss watchdog + legacy light-curve fidelity (M11)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from astropy.io import fits

from ecallisto_ng.core import (
    Channel,
    Recording,
    RecordingMeta,
    SpectrumFrame,
)
from ecallisto_ng.core.spectra import Capabilities, InstrumentInfo
from ecallisto_ng.core.units import (
    InstrumentClass,
    LinkKind,
    ProcessingLocation,
    UnitLevel,
)
from ecallisto_ng.services.acquisition import record
from ecallisto_ng.services.lightcurve import write_light_curves
from ecallisto_ng.services.watchdog import (
    AUTO_START,
    CHECK_RS232,
    DATA_LOSS,
    DataLossError,
    Watchdog,
)
from ecallisto_ng.writers.fits import StandardFitsWriter


def test_watchdog_flags_out_of_range() -> None:
    wd = Watchdog(max_value=255)
    assert wd.check((10, 20, 30)) is None
    assert wd.check((10, 999, 30)) == CHECK_RS232  # high-byte corruption
    assert wd.check((-1, 5)) == CHECK_RS232
    assert wd.alert_sequence() == [DATA_LOSS, CHECK_RS232, AUTO_START]


class _CorruptingDriver:
    """Yields good sweeps, then one corrupt sweep at ``bad_at``."""

    def __init__(self, channels: int, bad_at: int) -> None:
        self._n = channels
        self._bad_at = bad_at
        self._i = 0

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            instrument_class=InstrumentClass.HETERODYNE,
            processing_location=ProcessingLocation.HOST,
            link=LinkKind.USB,
            bands_mhz=((45.0, 870.0),),
            max_channels=512,
            bit_depth=8,
            max_sample_rate_hz=1000.0,
        )

    def connect(self) -> None:
        pass

    def identify(self) -> InstrumentInfo:
        return InstrumentInfo(model="FAKE", firmware="x")

    def configure(self, channels: object, rate: float) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def close(self) -> None:
        pass

    def stream(self) -> Iterator[SpectrumFrame]:
        while True:
            corrupt = self._i == self._bad_at
            val = 999 if corrupt else (self._i % 100)
            yield SpectrumFrame(
                timestamp_utc=datetime(2026, 6, 25, tzinfo=UTC),
                monotonic_ns=self._i,
                values=tuple([val] * self._n),
            )
            self._i += 1

    def overview(self) -> Iterator[SpectrumFrame]:
        yield from self.stream()


def test_record_stops_on_data_loss_and_alerts(tmp_path: Path) -> None:
    events: list[list[str]] = []
    chans = [Channel(frequency_mhz=45.0 + i) for i in range(4)]
    path = record(
        _CorruptingDriver(4, bad_at=3),
        StandardFitsWriter(),
        chans,
        RecordingMeta(instrument="WD"),
        tmp_path,
        sweeps_per_second=4.0,
        max_frames=20,
        watchdog=Watchdog(),
        on_data_loss=events.append,
    )
    # stopped early at the corrupt sweep -> 3 good frames written
    assert events == [[DATA_LOSS, CHECK_RS232, AUTO_START]]
    with fits.open(path) as hdul:
        assert hdul[0].data.shape == (4, 3)


def test_record_raises_when_first_sweep_is_lost(tmp_path: Path) -> None:
    with pytest.raises(DataLossError):
        record(
            _CorruptingDriver(4, bad_at=0),
            StandardFitsWriter(),
            [Channel(frequency_mhz=45.0 + i) for i in range(4)],
            RecordingMeta(instrument="WD"),
            tmp_path,
            sweeps_per_second=4.0,
            max_frames=20,
            watchdog=Watchdog(),
        )


def _recording(unit: UnitLevel) -> Recording:
    chans = tuple(
        Channel(frequency_mhz=100.0 + i, light_curve=(i % 2 == 0))
        for i in range(24)  # 12 flagged -> capped to 10
    )
    frames = tuple(
        SpectrumFrame(
            timestamp_utc=datetime(2026, 6, 25, 6, 30, tzinfo=UTC),
            monotonic_ns=i,
            values=tuple(range(24)),
        )
        for i in range(3)
    )
    return Recording(
        meta=RecordingMeta(instrument="ALASKA"),
        channels=chans,
        frames=frames,
        sample_rate_hz=4.0,
        unit=unit,
    )


def test_light_curve_legacy_name_and_cap(tmp_path: Path) -> None:
    path = write_light_curves(_recording(UnitLevel.RAW), tmp_path)
    assert path is not None
    assert path.name == "LC20260625_ADU_ALASKA.txt"  # legacy naming
    lines = path.read_text().splitlines()
    header = lines[0].split(",")
    assert header[0] == "Time[UT.hours]"
    assert len(header) == 1 + 10  # capped at 10 channels
    assert len(lines) == 1 + 3  # header + 3 sweeps
    assert lines[1].split(",")[0] == "6.5"  # 06:30 UT -> 6.5 h


def test_light_curve_unit_tag_sfu(tmp_path: Path) -> None:
    path = write_light_curves(_recording(UnitLevel.SFU), tmp_path)
    assert path is not None and "_SFU_" in path.name
