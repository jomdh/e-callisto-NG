# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-process live-frame bridge (localhost UDP)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from queue import Empty

from ecallisto_ng.core.spectra import SpectrumFrame
from ecallisto_ng.services.hub import FrameHub


def _frame(v: list[int]) -> SpectrumFrame:
    return SpectrumFrame(
        timestamp_utc=datetime(2026, 6, 26, tzinfo=UTC),
        monotonic_ns=123,
        values=v,
    )


def test_forwarded_frame_reaches_a_remote_subscriber() -> None:
    # "web" hub listens; a subscriber drains it. "daemon" hub forwards.
    web = FrameHub()
    port = 8767
    web.start_listener(port)
    q = web.subscribe(7)

    daemon = FrameHub()
    daemon.enable_forward("127.0.0.1", port)
    daemon.publish(7, _frame([1, 2, 3]))

    got = None
    for _ in range(50):  # up to ~1s for the datagram to arrive
        try:
            got = q.get_nowait()
            break
        except Empty:
            time.sleep(0.02)
    assert got is not None
    assert list(got.values) == [1, 2, 3]
    assert got.timestamp_utc == datetime(2026, 6, 26, tzinfo=UTC)
