# SPDX-License-Identifier: AGPL-3.0-or-later
"""First-class instrument liveness (ADR-0012).

``RECORDING`` is aspirational -- it is set when the record loop starts, not
while frames flow. A frame heartbeat (``RecorderRuntime.last_frame_at``,
stamped by the recorder) makes it empirical: a recording instrument that has
not produced a frame within a cadence-relative bound is **STALLED**.

This is the one liveness truth every consumer reads -- the dashboard cockpit,
the live WebSocket, diagnostics, and (opt-in) the auto-recover watchdog --
instead of each guessing from a different fragile proxy (file mtime, a thread
flag, an empty canvas). The recorder buffers a whole file in RAM between
rollovers, so file age can be many minutes stale while perfectly healthy; the
heartbeat is the only near-real-time signal.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ecallisto_ng.api.models import RecorderRuntime
from ecallisto_ng.api.settings import get_settings

STALLED = "stalled"

# A recording is stalled after this many missed sweeps (cadence-relative), but
# never sooner than the configured grace -- the driver self-heals first.
_STALL_SWEEPS = 8.0


def stall_bound_seconds(sweep_rate_hz: float) -> float:
    """How long without a frame before a recording instrument is STALLED."""
    grace = get_settings().stall_grace_seconds
    by_cadence = _STALL_SWEEPS / sweep_rate_hz if sweep_rate_hz > 0 else 0.0
    return max(grace, by_cadence)


def _age_seconds(when: datetime | None, now: datetime) -> float | None:
    if when is None:
        return None
    if when.tzinfo is None:  # SQLite may hand back a naive datetime
        when = when.replace(tzinfo=UTC)
    return (now - when).total_seconds()


def frame_age_seconds(
    row: RecorderRuntime, now: datetime | None = None
) -> float | None:
    """Seconds since the last frame heartbeat, or None if never stamped."""
    return _age_seconds(row.last_frame_at, now or datetime.now(UTC))


def is_stalled(
    row: RecorderRuntime,
    sweep_rate_hz: float,
    now: datetime | None = None,
) -> bool:
    """True if this instrument claims RECORDING but frames have stopped."""
    if row.state != "recording":
        return False
    now = now or datetime.now(UTC)
    bound = stall_bound_seconds(sweep_rate_hz)
    age = frame_age_seconds(row, now)
    if age is None:
        # No frame ever produced -- measure from when RECORDING was written, so
        # a just-started recording isn't flagged, but a mute-from-the-start one
        # is once it passes the bound.
        age = _age_seconds(row.updated_at, now)
    return age is not None and age > bound


def effective_state(
    row: RecorderRuntime,
    sweep_rate_hz: float,
    now: datetime | None = None,
) -> str:
    """The instrument's run-state with STALLED derived from the heartbeat."""
    return STALLED if is_stalled(row, sweep_rate_hz, now) else row.state
