"""Recorded-file catalog: scan the data dir, read headers, make quicklooks.

Scan-based on purpose -- the FITS files on disk are the source of truth, so
there is no index to drift. Quicklook PNGs are generated lazily and cached.
Lives in ``services`` and depends on no ``api`` model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits
from PIL import Image


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
