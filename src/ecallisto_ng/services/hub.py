# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live-frame pub/sub bridging the recorder to WebSocket clients.

The recorder (a worker thread) publishes spectra; WebSocket clients subscribe
and drain their own bounded queue. Slow clients drop frames rather than block
acquisition -- the authoritative record is always the FITS on disk, live frames
are ephemeral (DESIGN 11).

When acquisition runs in a separate process (the ``acquire`` daemon, ADR-0007)
the frames must still reach the WebSocket feed in the web app. The hub bridges
them over a **localhost UDP datagram** -- loss-tolerant by design: the daemon
calls :meth:`enable_forward`, the web app calls :meth:`start_listener`, and a
forwarded frame is re-published locally to the WS subscribers.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
from datetime import datetime
from queue import Empty, Full, Queue

from ecallisto_ng.core.spectra import SpectrumFrame
from ecallisto_ng.core.units import UnitLevel

_QUEUE_MAX = 256
_MAX_DATAGRAM = 60000  # safe UDP payload (< 65507) for the live bridge
_log = logging.getLogger(__name__)


class FrameHub:
    """Per-instrument fan-out of live frames to subscriber queues."""

    def __init__(self) -> None:
        self._subs: dict[int, list[Queue[SpectrumFrame]]] = {}
        self._lock = threading.Lock()
        self._forward: tuple[str, int] | None = None
        self._send_sock: socket.socket | None = None
        self._listening = False
        self._warned_oversize = False

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
        self._publish_local(instrument_id, frame)
        if self._forward is not None:
            self._forward_frame(instrument_id, frame)

    def _publish_local(self, instrument_id: int, frame: SpectrumFrame) -> None:
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

    # -- cross-process bridge (localhost UDP) ------------------------------

    def enable_forward(self, host: str, port: int) -> None:
        """Forward every published frame to a peer hub's UDP listener.

        Called by the acquire daemon so its recorded frames reach the web
        app's WebSocket feed.
        """
        self._forward = (host, port)
        self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _forward_frame(self, instrument_id: int, frame: SpectrumFrame) -> None:
        if self._send_sock is None or self._forward is None:
            return
        try:
            payload = json.dumps(
                {
                    "iid": instrument_id,
                    "t": frame.timestamp_utc.isoformat(),
                    "mono": frame.monotonic_ns,
                    "values": list(frame.values),
                    "unit": frame.unit.value,
                    "fc": frame.focus_code,
                }
            ).encode("utf-8")
            if len(payload) > _MAX_DATAGRAM:
                if not self._warned_oversize:
                    self._warned_oversize = True
                    _log.warning(
                        "live frame too large for the UDP bridge (%d bytes, "
                        "%d channels) -- live view unavailable for instrument "
                        "%s over the two-process bridge",
                        len(payload),
                        len(frame.values),
                        instrument_id,
                    )
                return
            self._send_sock.sendto(payload, self._forward)
        except OSError:
            pass  # best-effort; live frames are ephemeral

    def start_listener(self, port: int) -> None:
        """Receive forwarded frames on localhost UDP + re-publish locally.

        Called by the web app so frames recorded in the acquire daemon reach
        its WebSocket subscribers. Idempotent.
        """
        if self._listening:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
        except OSError as exc:  # pragma: no cover - env-dependent
            _log.warning("live bridge listener not started: %s", exc)
            return
        self._listening = True

        def _serve() -> None:
            while True:
                try:
                    data, _ = sock.recvfrom(65535)
                    self._ingest(data)
                except OSError:  # pragma: no cover - socket teardown
                    break

        threading.Thread(target=_serve, daemon=True).start()

    def _ingest(self, data: bytes) -> None:
        try:
            msg = json.loads(data.decode("utf-8"))
            iid = int(msg["iid"])
            frame = SpectrumFrame(
                timestamp_utc=datetime.fromisoformat(msg["t"]),
                monotonic_ns=int(msg.get("mono", 0)),
                values=list(msg["values"]),
                unit=UnitLevel(msg.get("unit", UnitLevel.RAW.value)),
                focus_code=int(msg.get("fc", 0)),
            )
        except (ValueError, KeyError, TypeError):
            return  # ignore a malformed datagram -- keep the listener alive
        self._publish_local(iid, frame)


# re-export for callers that drain queues
__all__ = ["FrameHub", "Empty", "get_hub"]

_hub = FrameHub()


def get_hub() -> FrameHub:
    return _hub
