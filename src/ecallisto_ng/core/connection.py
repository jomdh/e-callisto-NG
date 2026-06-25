# SPDX-License-Identifier: AGPL-3.0-or-later
"""Device-connection seam.

A driver reaches its instrument through a ``Connection`` -- the device-side
transport (DESIGN 5a). The medium varies by instrument class: serial-over-USB
(class-1 e-Callisto), USB bulk (class-2 SDR), TCP/Ethernet (class-3 FPGA). The
driver depends only on this small interface, so the same driver logic is
testable against a simulator and runnable against real hardware.

This is distinct from :class:`ecallisto_ng.core.UploadTransport`, which is the
*outbound* (file-shipping) seam.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Connection(Protocol):
    """A byte-oriented, bidirectional link to one instrument."""

    def write(self, data: bytes) -> None:
        """Send bytes to the device."""

    def read(self, size: int = 1, timeout: float | None = None) -> bytes:
        """Read up to ``size`` bytes.

        Returns the bytes available (possibly fewer than ``size``, possibly
        empty on timeout). Never blocks longer than ``timeout`` seconds when
        given; ``None`` means use the connection's default.
        """

    def close(self) -> None:
        """Release the link."""
