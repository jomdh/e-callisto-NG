"""End-to-end record loop: driver -> FITS on disk, for fake and Callisto."""

from __future__ import annotations

from pathlib import Path

from astropy.io import fits

from ecallisto_ng.core import Channel, RecordingMeta
from ecallisto_ng.drivers.callisto import (
    CallistoConfig,
    CallistoDriver,
    SimulatedCallisto,
)
from ecallisto_ng.drivers.fake import FakeDriver
from ecallisto_ng.services.acquisition import record, record_continuous
from ecallisto_ng.writers.fits import StandardFitsWriter


def _channels(n: int) -> tuple[Channel, ...]:
    return tuple(Channel(frequency_mhz=45.0 + i) for i in range(n))


def test_record_continuous_rolls_files_and_flushes_partial(
    tmp_path: Path,
) -> None:
    # Stream until Stop, rolling a file every 4 sweeps; stop after 10 sweeps so
    # we get files of 4 + 4 + a partial 2 (degrade, don't die). An advancing
    # clock gives each rolled file a distinct (per-second) FITS name, as a real
    # 15-min rollover would.
    from datetime import UTC, datetime, timedelta

    ticks = [0]

    def _clock() -> datetime:
        t = datetime(2026, 6, 25, 10, 0, 0, tzinfo=UTC) + timedelta(
            seconds=ticks[0]
        )
        ticks[0] += 1
        return t

    driver = FakeDriver(channels=8, clock=_clock)
    seen = 0

    def _stop_after_ten(_frame: object) -> None:
        nonlocal seen
        seen += 1
        if seen >= 10:
            driver.stop()

    paths = record_continuous(
        driver,
        StandardFitsWriter(),
        _channels(8),
        RecordingMeta(instrument="FAKESTN", focus_code=1),
        tmp_path,
        sweeps_per_second=4.0,
        frames_per_file=4,
        on_frame=_stop_after_ten,
    )
    assert len(paths) == 3  # 4, 4, partial 2
    shapes = [fits.open(p)[0].data.shape for p in paths]
    assert shapes == [(8, 4), (8, 4), (8, 2)]
    # distinct filenames per rolled file
    assert len({p.name for p in paths}) == 3


def test_record_with_fake_driver(tmp_path: Path) -> None:
    meta = RecordingMeta(instrument="FAKESTN", focus_code=1)
    path = record(
        FakeDriver(channels=16),
        StandardFitsWriter(),
        _channels(16),
        meta,
        tmp_path,
        sweeps_per_second=4.0,
        max_frames=10,
    )
    assert path.exists()
    with fits.open(path) as hdul:
        assert hdul[0].data.shape == (16, 10)  # (freq, time)
        assert hdul[0].header["INSTRUME"] == "FAKESTN"
        assert hdul[0].header["CDELT1"] == 0.25


def test_record_with_callisto_sim(tmp_path: Path) -> None:
    driver = CallistoDriver(
        SimulatedCallisto("1.8"), config=CallistoConfig(focuscode=2)
    )
    meta = RecordingMeta(instrument="CALSTN", focus_code=2)
    path = record(
        driver,
        StandardFitsWriter(),
        _channels(32),
        meta,
        tmp_path,
        sweeps_per_second=4.0,
        max_frames=8,
    )
    assert path.exists()
    with fits.open(path) as hdul:
        assert hdul[0].data.shape == (32, 8)
        # B1: time axis is 1/sweeps-per-second regardless of channel count
        assert hdul[0].header["CDELT1"] == 0.25
        assert hdul[0].header["INSTRUME"] == "CALSTN"


def test_record_rejects_zero_frames(tmp_path: Path) -> None:
    try:
        record(
            FakeDriver(channels=4),
            StandardFitsWriter(),
            _channels(4),
            RecordingMeta(instrument="X"),
            tmp_path,
            sweeps_per_second=4.0,
            max_frames=0,
        )
    except ValueError:
        return
    raise AssertionError("max_frames=0 should be rejected")
