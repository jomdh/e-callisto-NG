"""Recorded-file catalog: scan the data dir, read headers, make quicklooks.

Scan-based on purpose -- the FITS files on disk are the source of truth, so
there is no index to drift. Quicklook PNGs are generated lazily and cached.
Lives in ``services`` and depends on no ``api`` model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits
from PIL import Image

_DATE_RE = re.compile(r"_(\d{8})_")


@dataclass(frozen=True)
class FileInfo:
    name: str
    instrument: str
    date_obs: str
    rows: int  # frequency
    cols: int  # time
    size_bytes: int


def list_recordings(data_dir: Path) -> list[FileInfo]:
    """List FITS recordings in ``data_dir``, newest first."""
    out: list[FileInfo] = []
    if not data_dir.exists():
        return out
    for path in sorted(data_dir.glob("*.fit"), reverse=True):
        try:
            header = fits.getheader(path, 0)
            out.append(
                FileInfo(
                    name=path.name,
                    instrument=str(header.get("INSTRUME", "")),
                    date_obs=str(header.get("DATE-OBS", "")),
                    rows=int(header.get("NAXIS2", 0)),
                    cols=int(header.get("NAXIS1", 0)),
                    size_bytes=path.stat().st_size,
                )
            )
        except Exception:  # noqa: BLE001 - skip unreadable files
            continue
    return out


def resolve_in(data_dir: Path, name: str) -> Path | None:
    """Resolve ``name`` to a file directly inside ``data_dir``, or None.

    Rejects path traversal: only a basename whose parent is the data dir.
    """
    if "/" in name or "\\" in name or name in ("", ".", ".."):
        return None
    path = (data_dir / name).resolve()
    if path.parent != data_dir.resolve() or not path.is_file():
        return None
    return path


def quicklook_png(fits_path: Path, quicklook_dir: Path) -> Path:
    """Return a cached grayscale PNG of the FITS image (generate if absent)."""
    quicklook_dir.mkdir(parents=True, exist_ok=True)
    png_path = quicklook_dir / (fits_path.stem + ".png")
    if png_path.exists():
        return png_path
    with fits.open(fits_path) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.uint8)
    Image.fromarray(data, mode="L").save(png_path)
    return png_path


def recordings_by_day(data_dir: Path) -> dict[str, int]:
    """Count recordings per ``YYYY-MM-DD`` (from the filename date)."""
    counts: dict[str, int] = {}
    if not data_dir.is_dir():
        return counts
    for path in data_dir.glob("*.fit"):
        m = _DATE_RE.search(path.name)
        if not m:
            continue
        d = m.group(1)
        key = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def fits_header(fits_path: Path) -> dict[str, str]:
    """Selected primary-header cards as strings (for the in-browser viewer)."""
    keys = (
        "INSTRUME",
        "DATE-OBS",
        "TIME-OBS",
        "TIME-END",
        "BUNIT",
        "NAXIS1",
        "NAXIS2",
        "CDELT1",
        "CDELT2",
        "FRQFILE",
        "PWM",
        "OBS_LAT",
        "OBS_LON",
    )
    header = fits.getheader(fits_path, 0)
    return {k: str(header[k]) for k in keys if k in header}
