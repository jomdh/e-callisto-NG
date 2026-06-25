# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parse 2-column ASCII spectra (legacy M9703APlotter parity, M13).

The legacy viewer opens ``.prn``/``.csv``/``.txt`` files of ``frequency,
amplitude`` pairs, auto-detecting the delimiter (comma / semicolon / space) and
skipping one header line. ``parse_two_column`` mirrors that; ``list_spectra``
finds candidate files in the data dir (overviews + generic 2-column files).
"""

from __future__ import annotations

from pathlib import Path

_SUFFIXES = (".prn", ".csv", ".txt")


def parse_two_column(text: str) -> tuple[list[float], list[float]]:
    """Return (frequencies, amplitudes); skip the header, auto-detect delim."""
    freqs: list[float] = []
    amps: list[float] = []
    for line in text.splitlines()[1:]:  # skip one header row
        line = line.strip()
        if not line:
            continue
        if "," in line:
            parts = line.split(",")
        elif ";" in line:
            parts = line.split(";")
        else:
            parts = line.split()
        if len(parts) < 2:
            continue
        try:
            freqs.append(float(parts[0]))
            amps.append(float(parts[1]))
        except ValueError:
            continue
    return freqs, amps


def list_spectra(data_dir: Path) -> list[str]:
    """Names of 2-column spectrum files in the data dir (sorted)."""
    if not data_dir.is_dir():
        return []
    names = [
        p.name
        for p in data_dir.iterdir()
        if p.is_file() and p.suffix.lower() in _SUFFIXES
    ]
    return sorted(names)
