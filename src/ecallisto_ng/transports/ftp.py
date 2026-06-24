"""FTP transport (stdlib ftplib).

Uploads to a ``.tmp`` name then renames, matching the legacy upload scripts so
the server never serves a partial file. ``ftplib`` is stdlib, but the
connection is opened lazily so import is cheap and offline tests need nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FtpTransport:
    """A ``UploadTransport`` over plain FTP."""

    def __init__(
        self,
        host: str,
        username: str = "",
        password: str = "",
        base_path: str = "/",
        timeout: float = 30.0,
    ) -> None:
        self._host = host
        self._user = username
        self._password = password
        self._base = base_path.rstrip("/")
        self._timeout = timeout
        self._ftp: Any = None

    def connect(self) -> None:
        from ftplib import FTP

        ftp = FTP(timeout=self._timeout)
        ftp.connect(self._host)
        ftp.login(self._user, self._password)
        if self._base:
            ftp.cwd(self._base)
        self._ftp = ftp

    def put(self, local: Path, remote: str) -> None:
        assert self._ftp is not None, "connect() first"
        tmp = remote + ".tmp"
        with local.open("rb") as fh:
            self._ftp.storbinary(f"STOR {tmp}", fh)
        self._ftp.rename(tmp, remote)

    def verify(self, local: Path, remote: str) -> bool:
        assert self._ftp is not None, "connect() first"
        try:
            size = self._ftp.size(remote)
        except Exception:  # noqa: BLE001 - server may not support SIZE
            return True
        return size is None or size == local.stat().st_size

    def close(self) -> None:
        if self._ftp is not None:
            try:
                self._ftp.quit()
            except Exception:  # noqa: BLE001 - best effort
                pass
            self._ftp = None
