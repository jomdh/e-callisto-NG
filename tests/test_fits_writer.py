"""StandardFitsWriter: round-trip a recording through FITS and read it back."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from astropy.io import fits

from ecallisto_ng.core import (
    Channel,
    OutputWriter,
    Recording,
    RecordingMeta,
    SpectrumFrame,
)
from ecallisto_ng.writers.fits import StandardFitsWriter


def _recording(n_frames: int = 6, n_channels: int = 4) -> Recording:
    start = datetime(2026, 6, 25, 10, 30, 0, tzinfo=UTC)
    channels = tuple(
        Channel(frequency_mhz=100.0 + 10.0 * i) for i in range(n_channels)
    )
    frames = tuple(
        SpectrumFrame(
            timestamp_utc=start,
            monotonic_ns=i,
            values=tuple((i + c) % 256 for c in range(n_channels)),
        )
        for i in range(n_frames)
    )
    meta = RecordingMeta(
        instrument="TESTSTN",
        origin="Test Observatory",
        latitude_deg=-33.5,
        longitude_deg=151.2,
        altitude_m=22.0,
        frqfile="frq00001.cfg",
        pwm=120,
        focus_code=1,
    )
    return Recording(
        meta=meta, channels=channels, frames=frames, sample_rate_hz=4.0
    )


def test_writer_conforms_to_contract() -> None:
    assert isinstance(StandardFitsWriter(), OutputWriter)


def test_filename_format() -> None:
    name = StandardFitsWriter().filename(_recording())
    assert name == "TESTSTN_20260625_103000_01.fit"


def test_fits_shape_and_values(tmp_path: Path) -> None:
    rec = _recording(n_frames=6, n_channels=4)
    path = StandardFitsWriter().write(rec, tmp_path)
    assert path.exists()

    with fits.open(path) as hdul:
        image = hdul[0].data
        # primary HDU is (freq, time) = (channels, frames), 8-bit
        assert image.shape == (4, 6)
        assert image.dtype == np.uint8
        # frequency reversed: top row is the lowest channel's *highest* freq?
        # low frequency on top -> row 0 corresponds to channels[0] (100 MHz)
        # after flip. Verify via the FREQUENCY axis column instead.
        freq = hdul[1].data["FREQUENCY"][0]
        assert list(freq) == [130.0, 120.0, 110.0, 100.0]
        time = hdul[1].data["TIME"][0]
        assert np.allclose(time, [0.0, 0.25, 0.5, 0.75, 1.0, 1.25])


def test_fits_header_cards(tmp_path: Path) -> None:
    rec = _recording()
    path = StandardFitsWriter().write(rec, tmp_path)
    with fits.open(path) as hdul:
        h = hdul[0].header
        assert h["INSTRUME"] == "TESTSTN"
        assert h["ORIGIN"] == "Test Observatory"
        assert h["BUNIT"] == "digits"  # raw ADC default (DESIGN 6b)
        assert h["OBS_LAT"] == 33.5 and h["OBS_LAC"] == "S"
        assert h["OBS_LON"] == 151.2 and h["OBS_LOC"] == "E"
        assert h["FRQFILE"] == "frq00001.cfg"
        assert h["PWM_VAL"] == 120
        assert h["CTYPE1"] == "Time [UT]"
        assert h["CDELT1"] == 0.25  # 1 / 4 Hz
        assert h["CTYPE2"] == "Frequency [MHz]"


def test_empty_recording_rejected(tmp_path: Path) -> None:
    rec = _recording()
    empty = Recording(
        meta=rec.meta,
        channels=rec.channels,
        frames=(),
        sample_rate_hz=4.0,
    )
    try:
        StandardFitsWriter().write(empty, tmp_path)
    except ValueError:
        return
    raise AssertionError("empty recording should be rejected")
