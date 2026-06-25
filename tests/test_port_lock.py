# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-instrument serial-port lock serializes hardware operations."""

from __future__ import annotations

import pytest

from ecallisto_ng.services import port_lock


def test_hold_excludes_concurrent() -> None:
    with port_lock.hold(1):
        assert port_lock.is_busy(1) is True
        with pytest.raises(port_lock.InstrumentBusy):
            with port_lock.hold(1):
                pass  # pragma: no cover
    # released after the block
    assert port_lock.is_busy(1) is False


def test_locks_are_per_instrument() -> None:
    with port_lock.hold(10):
        assert port_lock.is_busy(10) is True
        # a different instrument is independent
        assert port_lock.is_busy(11) is False
        with port_lock.hold(11):
            assert port_lock.is_busy(11) is True
