# SPDX-License-Identifier: AGPL-3.0-or-later
"""Legacy-mode FITS writer.

Subclasses the standard writer and adds the legacy archive's warning COMMENT
cards, so files are drop-in for the existing e-Callisto tooling (DESIGN 6a).
The image, axes, and core header are already archive-shaped; this restores the
legacy header annotations.
"""

from __future__ import annotations

import numpy as np
from astropy.io import fits

from ecallisto_ng.core.recording import Recording
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.writers.fits.standard import StandardFitsWriter

# Legacy BUNIT strings the JavaViewer / archive key on (FitsWrite.cpp:240-246).
_BUNIT_LEGACY = {
    UnitLevel.RAW: "digits",
    UnitLevel.DB: "dB",
    UnitLevel.SFU: "45*log(sfu+10)",
    UnitLevel.KELVIN: "40*log(Tant)",
}


class LegacyFitsWriter(StandardFitsWriter):
    """Byte-compatible FITS for the legacy e-Callisto archive."""

    def _bunit(self, unit: UnitLevel) -> str:
        return _BUNIT_LEGACY[unit]  # audit A3

    def _build_table(
        self,
        rows: int,
        cols: int,
        time_axis: np.ndarray,
        freq_axis: np.ndarray,
    ) -> fits.BinTableHDU:
        table = super()._build_table(rows, cols, time_axis, freq_axis)
        # audit A6: legacy writes unit scale/zero + an 8.3 display format.
        h = table.header
        h["TSCAL1"] = (1.0, "")
        h["TZERO1"] = (0.0, "")
        h["TSCAL2"] = (1.0, "")
        h["TZERO2"] = (0.0, "")
        h["TDISP1"] = ("D8.3", "display format")
        h["TDISP2"] = ("D8.3", "display format")
        return table

    def _fill_header(
        self,
        header: fits.Header,
        recording: Recording,
        rows: int,
        cols: int,
        dt: float,
        image: np.ndarray,
    ) -> None:
        super()._fill_header(header, recording, rows, cols, dt, image)
        header["COMMENT"] = "Warning: the value of CDELT1 may be rounded!"
        header["COMMENT"] = "Warning: the frequency axis may not be regular!"
        header["COMMENT"] = "Warning: the value of CDELT2 may be rounded!"
