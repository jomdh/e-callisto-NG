# SPDX-License-Identifier: AGPL-3.0-or-later
"""In-memory Callisto device -- a serial-level simulator.

``SimulatedCallisto`` implements the ``Connection`` interface and speaks
just enough of the receiver protocol to drive ``CallistoDriver``
end-to-end with no hardware: it answers the identify/firmware handshake,
acknowledges EEPROM channel writes, and streams synthetic hex sweeps between
``GE`` and ``GD``. This is the class-1 counterpart of the generic FakeDriver.
"""

from __future__ import annotations

import random

from ecallisto_ng.drivers.callisto import protocol as p

_STATUS_LINE = {
    "1.5": b"$CRX:ChargePump=on\r",
    "1.7": b"$CRX:Debug=off\r",
    "1.8": b"$CRX:V1.8 / 25.43MHz\r",
}


class SimulatedCallisto:
    """A fake receiver on the other end of a Connection."""

    def __init__(self, firmware: str = "1.8", seed: int = 0) -> None:
        if firmware not in _STATUS_LINE:
            raise ValueError(f"unknown firmware: {firmware}")
        self._firmware = firmware
        self._data10bit = firmware in ("1.7", "1.8")
        self._max_value = 1023 if self._data10bit else 255
        self._rng = random.Random(seed)
        self._cmd = bytearray()
        self._out = bytearray()
        self._running = False
        self._nchannels = 0
        self._sweep = 0

    # -- Connection interface ---------------------------------------------

    def write(self, data: bytes) -> None:
        self._cmd += data
        while b"\r" in self._cmd:
            idx = self._cmd.index(b"\r")
            token = bytes(self._cmd[:idx])
            del self._cmd[: idx + 1]
            self._handle(token)

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        if self._running and not self._out and self._nchannels > 0:
            self._emit_sweep()
        chunk = bytes(self._out[:size])
        del self._out[:size]
        return chunk

    def close(self) -> None:
        self._running = False

    # -- protocol handling -------------------------------------------------

    def _handle(self, token: bytes) -> None:
        text = token.decode("ascii", "replace")
        if text == "S0":
            self._out += p.ID_RESPONSE  # "$CRX:Stopped\r"
        elif text == "GD":
            if self._running:
                self._running = False
                self._out += p.DATA_END + b"$CRX:Stopped\r"
        elif text == "?":
            self._out += _STATUS_LINE[self._firmware]
        elif text.startswith("FE"):
            self._out += p.EEPROM_READY  # "]"
        elif text.startswith("L"):
            self._set_channels(text[1:])
        elif text == "S1":
            self._out += b"$CRX:Started\r"
        elif text == "GE":
            self._running = True
            self._sweep = 0
            self._out += p.DATA_START  # STX
        elif text == "P2":
            self._emit_overview()
        # D0, GS/GA, T/O/C, FS, M2, %5, F... -> acknowledged silently

    def _set_channels(self, rest: str) -> None:
        try:
            n = int(rest)
        except ValueError:
            return
        # L13200 is the overview "all channels" length, not a sweep size.
        if n != 13200:
            self._nchannels = n

    def _emit_sweep(self) -> None:
        center = self._sweep % self._nchannels
        width = max(self._nchannels / 12.0, 1.0)
        for ch in range(self._nchannels):
            dist = (ch - center) / width
            peak = self._max_value * pow(2.718281828, -0.5 * dist * dist)
            noise = self._rng.uniform(0, self._max_value * 0.08)
            value = int(min(self._max_value, peak + noise))
            self._out += f"{value:04X}".encode("ascii")
        self._sweep += 1

    def _emit_overview(self) -> None:
        freqs = [45.0, 145.0, 245.0, 345.0, 445.0, 600.0, 750.0, 870.0]
        for freq in freqs:
            amp = self._rng.randint(100, 2000)
            self._out += f"$CRX:{freq:.3f},{amp}\r".encode("ascii")
