# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-instrument serial-port lock.

One physical device, one operation at a time. Record, overview, diagnose, and
the bench tools all open the same serial port; two at once collide (pyserial:
"device reports readiness to read but returned no data ... multiple access on
port"). This process-wide, per-instrument lock serializes them so a second
operation gets a clean "busy" instead of a corrupt read.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

_locks: dict[int, threading.Lock] = {}
_guard = threading.Lock()


class InstrumentBusy(Exception):
    """Raised when the instrument's port is already in use."""


def _lock_for(instrument_id: int) -> threading.Lock:
    with _guard:
        return _locks.setdefault(instrument_id, threading.Lock())


@contextmanager
def hold(instrument_id: int) -> Iterator[None]:
    """Hold the instrument's port for the duration, or raise InstrumentBusy."""
    lock = _lock_for(instrument_id)
    if not lock.acquire(blocking=False):
        raise InstrumentBusy(instrument_id)
    try:
        yield
    finally:
        lock.release()


def is_busy(instrument_id: int) -> bool:
    """True if another operation currently holds the instrument's port."""
    lock = _lock_for(instrument_id)
    if lock.acquire(blocking=False):
        lock.release()
        return False
    return True
