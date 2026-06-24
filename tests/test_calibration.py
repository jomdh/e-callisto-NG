"""Calibration math + calibrated FITS output."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from astropy.io import fits

from ecallisto_ng.core import (
    Calibration,
    Channel,
    ChannelCal,
    Recording,
    RecordingMeta,
    SpectrumFrame,
    UnitLevel,
)
from ecallisto_ng.core.calibration import to_kelvin, to_sfu
from ecallisto_ng.writers.fits import StandardFitsWriter


def test_sfu_kelvin_in_range() -> None:
    c = ChannelCal(a=10.0, b=40.0, cf=1.0, tb=2.7)
    for adc in (0, 64, 128, 200, 255):
        assert 0 <= to_sfu(adc, c) <= 255
        assert 0 <= to_kelvin(adc, c) <= 255
    # higher ADC -> higher (or equal) calibrated value (monotone-ish)
    assert to_sfu(200, c) >= to_sfu(20, c)


def _recording(unit: UnitLevel, cal: Calibration | None) -> Recording:
    chans = tuple(Channel(frequency_mhz=100.0 + i) for i in range(4))
    frames = tuple(
        SpectrumFrame(
            timestamp_utc=datetime(2026, 6, 25, tzinfo=UTC),
            monotonic_ns=i,
            values=(50, 120, 180, 240),
        )
        for i in range(3)
    )
    return Recording(
        meta=RecordingMeta(instrument="CAL"),
        channels=chans,
        frames=frames,
        sample_rate_hz=4.0,
        unit=unit,
        calibration=cal,
    )


def test_writer_raw_vs_calibrated(tmp_path: Path) -> None:
    cal = Calibration(
        channels=tuple(ChannelCal(10.0, 40.0, 1.0, 2.7) for _ in range(4))
    )
    raw_dir = tmp_path / "raw"
    sfu_dir = tmp_path / "sfu"
    raw_dir.mkdir()
    sfu_dir.mkdir()
    raw_path = StandardFitsWriter().write(
        _recording(UnitLevel.RAW, None), raw_dir
    )
    sfu_path = StandardFitsWriter().write(
        _recording(UnitLevel.SFU, cal), sfu_dir
    )

    with fits.open(raw_path) as r, fits.open(sfu_path) as s:
        assert r[0].header["BUNIT"] == "digits"
        assert s[0].header["BUNIT"] == "sfu"
        # calibrated pixels differ from raw
        assert (r[0].data != s[0].data).any()
