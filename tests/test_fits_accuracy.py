# SPDX-License-Identifier: AGPL-3.0-or-later
"""Byte-exact FITS fixes vs Borland FitsWrite.cpp (M26 A3/A6/A7)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from astropy.io import fits

from ecallisto_ng.core.calibration import Calibration, ChannelCal
from ecallisto_ng.core.recording import (
    Recording,
    RecordingMeta,
    SpectrumFrame,
)
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.writers.fits.legacy import LegacyFitsWriter
from ecallisto_ng.writers.fits.standard import StandardFitsWriter


def _recording(unit: UnitLevel, cal: Calibration | None) -> Recording:
    chans = tuple(Channel(frequency_mhz=45.0 + i) for i in range(4))
    t0 = datetime(2026, 6, 25, 10, 0, 0, tzinfo=UTC)
    frames = (
        SpectrumFrame(
            timestamp_utc=t0, monotonic_ns=0, values=(10, 20, 30, 40)
        ),
        SpectrumFrame(
            timestamp_utc=t0, monotonic_ns=1, values=(15, 25, 35, 45)
        ),
    )
    return Recording(
        meta=RecordingMeta(instrument="T1"),
        channels=chans,
        frames=frames,
        sample_rate_hz=4.0,
        unit=unit,
        calibration=cal,
    )


def _cal() -> Calibration:
    return Calibration(
        channels=tuple(
            ChannelCal(a=1.0, b=20.0, cf=1.0, tb=0.0) for _ in range(4)
        )
    )


def test_legacy_bunit_strings(tmp_path: Path) -> None:  # audit A3
    p = LegacyFitsWriter().write(_recording(UnitLevel.SFU, _cal()), tmp_path)
    with fits.open(p) as hdul:
        assert hdul[0].header["BUNIT"] == "45*log(sfu+10)"
    p2 = LegacyFitsWriter().write(
        _recording(UnitLevel.KELVIN, _cal()), tmp_path
    )
    with fits.open(p2) as hdul:
        assert hdul[0].header["BUNIT"] == "40*log(Tant)"
    # standard writer keeps the short strings
    ps = StandardFitsWriter().write(
        _recording(UnitLevel.SFU, _cal()), tmp_path
    )
    with fits.open(ps) as hdul:
        assert hdul[0].header["BUNIT"] == "sfu"


def test_legacy_table_scale_cards(tmp_path: Path) -> None:  # audit A6
    p = LegacyFitsWriter().write(_recording(UnitLevel.RAW, None), tmp_path)
    with fits.open(p) as hdul:
        th = hdul[1].header
        assert th["TSCAL1"] == 1.0 and th["TZERO1"] == 0.0
        assert th["TSCAL2"] == 1.0 and th["TZERO2"] == 0.0
        assert th["TDISP1"] == "D8.3" and th["TDISP2"] == "D8.3"
    ps = StandardFitsWriter().write(_recording(UnitLevel.RAW, None), tmp_path)
    with fits.open(ps) as hdul:
        assert "TSCAL1" not in hdul[1].header


def test_datamin_over_written_image(tmp_path: Path) -> None:  # audit A7
    p = StandardFitsWriter().write(_recording(UnitLevel.RAW, None), tmp_path)
    with fits.open(p) as hdul:
        data = hdul[0].data
        assert hdul[0].header["DATAMIN"] == int(data.min())
        assert hdul[0].header["DATAMAX"] == int(data.max())
