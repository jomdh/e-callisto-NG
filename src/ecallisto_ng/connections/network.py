"""TCP/Ethernet connection backend (class-3 FPGA appliances, DESIGN 5a).

Implements :class:`ecallisto_ng.core.connection.Connection` over a TCP socket.
The socket is opened lazily; offline tests use the in-memory FPGA simulator
instead, so no network is required.
"""

from __future__ import annotations

import socket


class NetworkConnection:
    """A ``Connection`` backed by a TCP socket (``host:port``)."""

    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        self._sock = socket.create_connection(
            (self._host, self._port), timeout=self._timeout
        )

    def write(self, data: bytes) -> None:
        assert self._sock is not None, "connect() first"
        self._sock.sendall(data)

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        assert self._sock is not None, "connect() first"
        if timeout is not None:
            self._sock.settimeout(timeout)
        try:
            return self._sock.recv(size)
        except TimeoutError:  # pragma: no cover - env-dependent
            return b""

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None
