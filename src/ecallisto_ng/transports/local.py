"""Local-directory transport (copy/mirror to a folder or mounted drive).

Useful on its own (mirror to a USB/NAS path) and as the testable reference
implementation of the ``UploadTransport`` contract. Uses the tmp-then-rename
handshake so a reader never sees a partial file.
"""

from __future__ import annotations

import shutil
from pathlib import Path


class LocalTransport:
    """Writes uploaded files into ``dest_dir``."""

    def __init__(self, dest_dir: str) -> None:
        self._dest = Path(dest_dir)

    def connect(self) -> None:
        self._dest.mkdir(parents=True, exist_ok=True)

    def put(self, local: Path, remote: str) -> None:
        target = self._dest / remote
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        shutil.copyfile(local, tmp)
        tmp.replace(target)

    def verify(self, local: Path, remote: str) -> bool:
        target = self._dest / remote
        return (
            target.is_file() and target.stat().st_size == local.stat().st_size
        )

    def close(self) -> None:
        pass
