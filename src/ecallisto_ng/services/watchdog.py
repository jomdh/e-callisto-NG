# SPDX-License-Identifier: AGPL-3.0-or-later
"""Data-loss watchdog (legacy callisto.exe parity, DESIGN 14a).

The Windows recorder auto-stops, warns, and auto-restarts when the serial
stream goes bad ("high-byte data appears unexpectedly"). NG mirrors that: the
watchdog flags a corrupt sweep, the recorder stops and alerts with the **exact
legacy strings** (so operator memory + support docs still apply), and the
scheduler's next tick re-arms the recording -- that re-arm *is* the auto-start.

The alert strings are quoted verbatim from `mainunit.cpp` (see
`docs/legacy/WINDOWS_UX.md` section 1).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

# Verbatim legacy log lines.
DATA_LOSS = "Auto stop due to data loss."
CHECK_RS232 = "Check RS232-connection!"
AUTO_START = "Attempting Auto-Start"
RECEIVER_RESET = "Watchdog triggered -> Reset"


class DataLossError(Exception):
    """Raised/flagged when the stream is judged corrupt and must stop."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class Watchdog:
    """Flags a sweep whose values fall outside the valid product range.

    ``max_value`` is the product ceiling (255 for an 8-bit spectrogram); a
    value above it is the NG equivalent of the legacy "high-byte" condition.
    """

    max_value: int = 255

    def check(self, values: Sequence[int]) -> str | None:
        """Return a data-loss reason if the sweep is corrupt, else None."""
        for v in values:
            if v < 0 or v > self.max_value:
                return CHECK_RS232
        return None

    def alert_sequence(self) -> list[str]:
        """The three-line legacy auto-stop/restart log sequence."""
        return [DATA_LOSS, CHECK_RS232, AUTO_START]
