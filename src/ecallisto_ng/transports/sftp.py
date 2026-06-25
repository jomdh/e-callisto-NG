"""SFTP transport (paramiko).

Mirrors the FTP transport: upload to a ``.tmp`` name then rename, so the
server never serves a partial file (legacy upload-script behaviour). The SSH
connection is opened lazily, so import is cheap and offline tests need none.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SftpTransport:
    """A ``UploadTransport`` over SFTP (SSH)."""

    def __init__(
        self,
        host: str,
        username: str = "",
        password: str = "",
        base_path: str = "/",
        port: int = 22,
        timeout: float = 30.0,
    ) -> None:
        self._host = host
        self._user = username
        self._password = password
        self._base = base_path.rstrip("/") or "."
        self._port = port
        self._timeout = timeout
        self._client: Any = None
        self._sftp: Any = None

    def connect(self) -> None:  # pragma: no cover - needs a live server
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self._host,
            port=self._port,
            username=self._user,
            password=self._password,
            timeout=self._timeout,
        )
        self._client = client
        self._sftp = client.open_sftp()

    def _remote(self, remote: str) -> str:
        return f"{self._base}/{remote}"

    def put(self, local: Path, remote: str) -> None:  # pragma: no cover
        assert self._sftp is not None, "connect() first"
        dest = self._remote(remote)
        tmp = dest + ".tmp"
        self._sftp.put(str(local), tmp)
        self._sftp.rename(tmp, dest)

    def verify(self, local: Path, remote: str) -> bool:  # pragma: no cover
        assert self._sftp is not None, "connect() first"
        try:
            size = self._sftp.stat(self._remote(remote)).st_size
        except OSError:
            return False
        return bool(size == local.stat().st_size)

    def close(self) -> None:  # pragma: no cover - needs a live server
        if self._sftp is not None:
            self._sftp.close()
            self._sftp = None
        if self._client is not None:
            self._client.close()
            self._client = None
