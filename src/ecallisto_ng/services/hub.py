"""In-memory live-frame pub/sub bridging the recorder thread to WS clients.

The recorder (a worker thread) publishes spectra; WebSocket clients subscribe
and drain their own bounded queue. Slow clients drop frames rather than block
acquisition -- the authoritative record is always the FITS on disk, live frames
are ephemeral (DESIGN 11).
"""

from __future__ import annotations

import threading
from queue import Empty, Full, Queue

from ecallisto_ng.core.spectra import SpectrumFrame

_QUEUE_MAX = 256


class FrameHub:
    """Per-instrument fan-out of live frames to subscriber queues."""

    def __init__(self) -> None:
        self._subs: dict[int, list[Queue[SpectrumFrame]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, instrument_id: int) -> Queue[SpectrumFrame]:
        q: Queue[SpectrumFrame] = Queue(maxsize=_QUEUE_MAX)
        with self._lock:
            self._subs.setdefault(instrument_id, []).append(q)
        return q

    def unsubscribe(self, instrument_id: int, q: Queue[SpectrumFrame]) -> None:
        with self._lock:
            subs = self._subs.get(instrument_id)
            if subs and q in subs:
                subs.remove(q)
                if not subs:
                    del self._subs[instrument_id]

    def publish(self, instrument_id: int, frame: SpectrumFrame) -> None:
        with self._lock:
            subs = list(self._subs.get(instrument_id, []))
        for q in subs:
            try:
                q.put_nowait(frame)
            except Full:
                pass  # drop for a slow client; never block the recorder

    def subscriber_count(self, instrument_id: int) -> int:
        with self._lock:
            return len(self._subs.get(instrument_id, []))


# re-export for callers that drain queues
__all__ = ["FrameHub", "Empty", "get_hub"]

_hub = FrameHub()


def get_hub() -> FrameHub:
    return _hub
