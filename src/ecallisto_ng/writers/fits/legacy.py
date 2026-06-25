# SPDX-License-Identifier: AGPL-3.0-or-later
"""Legacy-mode FITS writer.

Subclasses the standard writer and adds the legacy archive's warning COMMENT
cards, so files are drop-in for the existing e-Callisto tooling (DESIGN 6a).
The image, axes, and core header are already archive-shaped; this restores the
legacy header annotations.
"""

from __future__ import annotations

from astropy.io import fits

from ecallisto_ng.core.recording import Recording
from ecallisto_ng.writers.fits.standard import StandardFitsWriter


class LegacyFitsWriter(StandardFitsWriter):
    """Byte-compatible-leaning FITS for the legacy archive."""

    def _fill_header(
        self,
        header: fits.Header,
        recording: Recording,
        rows: int,
        cols: int,
        dt: float,
    ) -> None:
        super()._fill_header(header, recording, rows, cols, dt)
        header["COMMENT"] = "Warning: the value of CDELT1 may be rounded!"
        header["COMMENT"] = "Warning: the frequency axis may not be regular!"
        header["COMMENT"] = "Warning: the value of CDELT2 may be rounded!"
