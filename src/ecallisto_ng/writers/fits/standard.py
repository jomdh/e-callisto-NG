# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standard-mode FITS writer.

Writes a recording as a conventional 8-bit time x frequency FITS image with a
binary-table HDU carrying the time and frequency axes -- the e-Callisto archive
shape, without legacy header quirks. The frequency axis is reversed so the
lowest frequency is on the top row, matching the archive convention.

Units follow the recording (DESIGN 6b): ``BUNIT`` is ``digits`` for raw ADC.
``astropy``/``numpy`` are confined to this ``writers`` layer; ``core`` stays
dependency-free.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

import numpy as np
from astropy.io import fits

from ecallisto_ng.core.calibration import to_kelvin, to_sfu
from ecallisto_ng.core.recording import Recording
from ecallisto_ng.core.units import UnitLevel

_BUNIT = {
    UnitLevel.RAW: "digits",
    UnitLevel.DB: "dB",
    UnitLevel.SFU: "sfu",
    UnitLevel.KELVIN: "K",
}


def _calibrate(values: Sequence[int], recording: Recording) -> list[int]:
    """Per-channel calibrated samples, or raw if uncalibrated (DESIGN 6b)."""
    raw = list(values)
    cal = recording.calibration
    if recording.unit is UnitLevel.RAW or cal is None:
        return raw
    coeffs = cal.channels
    if recording.unit is UnitLevel.SFU:
        return [to_sfu(v, coeffs[i]) for i, v in enumerate(raw)]
    if recording.unit is UnitLevel.KELVIN:
        return [to_kelvin(v, coeffs[i]) for i, v in enumerate(raw)]
    return raw


class StandardFitsWriter:
    """Implements :class:`ecallisto_ng.core.OutputWriter` for standard FITS."""

    def filename(self, recording: Recording) -> str:
        start = recording.frames[0].timestamp_utc
        return (
            f"{recording.meta.instrument}_"
            f"{start:%Y%m%d_%H%M%S}_"
            f"{recording.meta.focus_code:02d}.fit"
        )

    def write(self, recording: Recording, out_dir: Path) -> Path:
        if not recording.frames:
            raise ValueError("recording has no frames")
        if not recording.channels:
            raise ValueError("recording has no channels")

        rows = len(recording.channels)  # frequency
        cols = len(recording.frames)  # time
        dt = 1.0 / recording.sample_rate_hz if recording.sample_rate_hz else 0

        # (time, freq) -> transpose, then flip freq so low is on top.
        samples = np.array(
            [_calibrate(f.values, recording) for f in recording.frames],
            dtype=np.uint8,
        )
        image = samples.T[::-1, :]

        path = out_dir / self.filename(recording)
        hdu = fits.PrimaryHDU(data=image)
        self._fill_header(hdu.header, recording, rows, cols, dt)

        time_axis = np.arange(cols, dtype=np.float64) * dt
        freq_axis = np.array(
            [c.frequency_mhz for c in recording.channels], dtype=np.float64
        )[::-1]
        table = fits.BinTableHDU.from_columns(
            [
                fits.Column(
                    name="TIME", format=f"{cols}D", array=time_axis[None, :]
                ),
                fits.Column(
                    name="FREQUENCY",
                    format=f"{rows}D",
                    array=freq_axis[None, :],
                ),
            ]
        )
        fits.HDUList([hdu, table]).writeto(path, overwrite=True)
        return path

    def _fill_header(
        self,
        header: fits.Header,
        recording: Recording,
        rows: int,
        cols: int,
        dt: float,
    ) -> None:
        meta = recording.meta
        start = recording.frames[0].timestamp_utc
        end = start + timedelta(seconds=cols * dt)
        image_min = min(min(f.values) for f in recording.frames)
        image_max = max(max(f.values) for f in recording.frames)

        header["DATE"] = (f"{start:%Y-%m-%d}", "Time of observation")
        # Long value -> no comment so the card fits in 80 chars.
        header["CONTENT"] = (
            f"{start:%Y/%m/%d}  Radio flux density, e-CALLISTO "
            f"({meta.instrument})"
        )
        header["ORIGIN"] = (meta.origin, "Organization name")
        header["TELESCOP"] = ("Radio Spectrometer", "Type of instrument")
        header["INSTRUME"] = (meta.instrument, "Name of the spectrometer")
        header["OBJECT"] = ("Sun", "object description")
        header["DATE-OBS"] = (f"{start:%Y/%m/%d}", "Date observation starts")
        header["TIME-OBS"] = (f"{start:%H:%M:%S.%f}"[:-3], "Time obs starts")
        header["DATE-END"] = (f"{end:%Y/%m/%d}", "Date observation ends")
        header["TIME-END"] = (f"{end:%H:%M:%S}", "Time observation ends")
        header["BZERO"] = (0.0, "scaling offset")
        header["BSCALE"] = (1.0, "scaling factor")
        header["BUNIT"] = (_BUNIT[recording.unit], "z-axis title")
        header["DATAMIN"] = (image_min, "minimum element in image")
        header["DATAMAX"] = (image_max, "maximum element in image")

        secs = start.hour * 3600 + start.minute * 60 + start.second
        header["CRVAL1"] = (float(secs), "axis 1 ref value [sec of day]")
        header["CRPIX1"] = (0, "reference pixel of axis 1")
        header["CTYPE1"] = ("Time [UT]", "title of axis 1")
        header["CDELT1"] = (dt, "step between elements on axis 1 [sec]")
        header["CRVAL2"] = (float(rows), "axis 2 ref value")
        header["CRPIX2"] = (0, "reference pixel of axis 2")
        header["CTYPE2"] = ("Frequency [MHz]", "title of axis 2")
        header["CDELT2"] = (-1.0, "step between elements on axis 2")

        header["OBS_LAT"] = (
            abs(meta.latitude_deg),
            "observatory latitude deg",
        )
        header["OBS_LAC"] = (
            "S" if meta.latitude_deg < 0 else "N",
            "latitude code {N,S}",
        )
        header["OBS_LON"] = (
            abs(meta.longitude_deg),
            "observatory longitude deg",
        )
        header["OBS_LOC"] = (
            "W" if meta.longitude_deg < 0 else "E",
            "longitude code {E,W}",
        )
        header["OBS_ALT"] = (meta.altitude_m, "observatory altitude m asl")
        header["FRQFILE"] = (meta.frqfile, "name of frequency file")
        header["PWM_VAL"] = (meta.pwm, "PWM value to control tuner gain")
