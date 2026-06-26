# SPDX-License-Identifier: AGPL-3.0-or-later
"""Incremental decoder for the Callisto byte stream.

Separates the two interleaved framings on the wire: text messages
(``$ ... \\r``) and hex sample data (STX ... ``&``). Samples are grouped into
sweeps of ``nchannels`` and normalized to 8 bits. Pure and incremental so it
is unit-testable byte-by-byte.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from ecallisto_ng.core.errors import RecoverableInstrumentError
from ecallisto_ng.drivers.callisto.protocol import (
    DATA_END,
    DATA_START,
    END_MARKER,
    MESSAGE_END,
    MESSAGE_START,
    to_8bit,
)

_HEX_DIGITS = frozenset(b"0123456789ABCDEF")


@dataclass(frozen=True)
class ParsedMessage:
    """A decoded text message (without the ``$``/``\\r`` framing)."""

    text: str


@dataclass(frozen=True)
class ParsedSweep:
    """One full sweep of 8-bit samples (length == nchannels)."""

    values: list[int]


class StreamParser:
    """Feed bytes in, get messages and completed sweeps out."""

    def __init__(self, nchannels: int, data10bit: bool) -> None:
        if nchannels < 1:
            raise ValueError("nchannels must be >= 1")
        self._nchannels = nchannels
        self._data10bit = data10bit
        self._in_data = False
        self._in_message = False
        self._message = bytearray()
        self._hexbuf = bytearray()
        self._sweep: list[int] = []

    def feed(self, data: bytes) -> Iterator[ParsedMessage | ParsedSweep]:
        for byte in data:
            yield from self._consume(byte)

    def _consume(self, byte: int) -> Iterator[ParsedMessage | ParsedSweep]:
        char = bytes([byte])

        if self._in_message:
            if char == MESSAGE_END:
                text = self._message.decode("ascii", "replace")
                self._in_message = False
                self._message = bytearray()
                yield ParsedMessage(text)
            else:
                self._message += char
            return

        # A text message ('$ ... \r') can interleave the data stream.
        if char == MESSAGE_START:
            self._in_message = True
            self._message = bytearray()
            return

        # ``DATA_START`` ('2') marks the start of hex data only when we're not
        # already in it -- once streaming, '2' is just a hex digit (legacy
        # callisto.c: ``if (!in_data && c == DATA_START)``).
        if not self._in_data and char == DATA_START:
            self._in_data = True
            self._hexbuf = bytearray()
            self._sweep = []
            return

        if self._in_data and char == DATA_END:
            self._in_data = False
            return

        if self._in_data and byte in _HEX_DIGITS:
            yield from self._consume_hex(byte)
        # Any other byte outside data (e.g. EEPROM_READY) is ignored here.

    def _consume_hex(self, byte: int) -> Iterator[ParsedSweep]:
        self._hexbuf.append(byte)
        if len(self._hexbuf) < 4:
            return
        value = int(self._hexbuf.decode("ascii"), 16)
        self._hexbuf = bytearray()
        if value == END_MARKER:
            return
        # Data-loss / framing check on the RAW value, before to_8bit clamps it
        # (legacy high-bit test): a valid sample fits the bit depth; high bits
        # set mean a dropped/shifted RS-232 byte -> the driver soft-resets.
        mask = 0x3FF if self._data10bit else 0xFF
        if value & ~mask:
            raise RecoverableInstrumentError(
                f"corrupt sample 0x{value:04X} (lost RS-232 framing)"
            )
        self._sweep.append(to_8bit(value, self._data10bit))
        if len(self._sweep) == self._nchannels:
            yield ParsedSweep(self._sweep)
            self._sweep = []
