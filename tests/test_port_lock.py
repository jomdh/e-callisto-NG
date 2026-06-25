# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-process per-instrument serial lock (flock)."""

from __future__ import annotations

import fcntl
import os

import pytest
from fastapi.testclient import TestClient

from ecallisto_ng.services import port_lock


def test_hold_excludes_concurrent(client: TestClient) -> None:
    with port_lock.hold(1):
        assert port_lock.is_busy(1) is True
        with pytest.raises(port_lock.InstrumentBusy):
            with port_lock.hold(1):
                pass  # pragma: no cover
    assert port_lock.is_busy(1) is False


def test_locks_are_per_instrument(client: TestClient) -> None:
    with port_lock.hold(10):
        assert port_lock.is_busy(10) is True
        assert port_lock.is_busy(11) is False  # independent device
        with port_lock.hold(11):
            assert port_lock.is_busy(11) is True


def test_busy_across_independent_holder(client: TestClient) -> None:
    # A separate fd holding the flock is exactly how another *process* holds it
    # (flock treats fds independently). Proves cross-process exclusion.
    path = port_lock._lock_path(42)
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        assert port_lock.is_busy(42) is True
        with pytest.raises(port_lock.InstrumentBusy):
            with port_lock.hold(42):
                pass  # pragma: no cover
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    assert port_lock.is_busy(42) is False
