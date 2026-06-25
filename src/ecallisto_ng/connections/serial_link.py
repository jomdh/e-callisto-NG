# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serial-over-USB connection backend (class-1 e-Callisto).

Implements :class:`ecallisto_ng.core.connection.Connection` over ``pyserial``.
``pyserial`` is imported lazily so the fake/simulator path and the test suite
do not require it.
"""

from __future__ import annotations

from typing import Any


class SerialConnection:
    """A ``Connection`` backed by a real serial port.

    The port is opened **lazily** on first I/O, not at construction: a driver
    can be built (e.g. to read its static ``capabilities``) without touching
    the hardware. The driver's ``connect()``/``close()`` lifecycle opens and
    releases the port -- so merely viewing an instrument never holds it open
    (which would block recording).
    """

    def __init__(
        self, port: str, baudrate: int = 115200, timeout: float = 1.0
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial: Any = None

    def _ensure_open(self) -> None:
        if self._serial is not None:
            return
        try:
            import serial
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "pyserial is required for serial connections: "
                "pip install pyserial"
            ) from exc
        self._serial = serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self._timeout,
        )

    def write(self, data: bytes) -> None:
        self._ensure_open()
        self._serial.write(data)

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        self._ensure_open()
        if timeout is not None:
            self._serial.timeout = timeout
        data: bytes = self._serial.read(size)
        return data

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None
