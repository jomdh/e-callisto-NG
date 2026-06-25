"""FITS output writers."""

from __future__ import annotations

from ecallisto_ng.core.contracts import OutputWriter
from ecallisto_ng.writers.fits.legacy import LegacyFitsWriter
from ecallisto_ng.writers.fits.standard import StandardFitsWriter

__all__ = ["StandardFitsWriter", "LegacyFitsWriter", "get_writer"]


def get_writer(mode: str) -> OutputWriter:
    """Pick the FITS writer for an output mode (DESIGN 6a).

    ``legacy`` adds the archive's warning cards; ``standard``/``custom``
    use the clean writer (custom naming templates are a future refinement).
    """
    if mode == "legacy":
        return LegacyFitsWriter()
    return StandardFitsWriter()
