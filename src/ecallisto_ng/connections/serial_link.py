"""Serial-over-USB connection backend (class-1 e-Callisto).

Implements :class:`ecallisto_ng.core.connection.Connection` over ``pyserial``.
``pyserial`` is imported lazily so the fake/simulator path and the test suite
do not require it.
"""

from __future__ import annotations

from typing import Any


class SerialConnection:
    """A ``Connection`` backed by a real serial port."""

    def __init__(
        self, port: str, baudrate: int = 115200, timeout: float = 1.0
    ) -> None:
        try:
            import serial
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "pyserial is required for serial connections: "
                "pip install pyserial"
            ) from exc
        self._serial: Any = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
        )

    def write(self, data: bytes) -> None:
        self._serial.write(data)

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        if timeout is not None:
            self._serial.timeout = timeout
        data: bytes = self._serial.read(size)
        return data

    def close(self) -> None:
        self._serial.close()
