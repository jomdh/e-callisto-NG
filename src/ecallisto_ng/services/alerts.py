"""Alert channels (DESIGN 5a extension point / 14a "always alert").

An ``AlertChannel`` delivers a short alert. Two real channels -- webhook (HTTP
POST) and email (SMTP) -- plus a fake for tests, all behind one protocol. The
network/SMTP calls are thin and pragma-excluded; ``dispatch`` is best-effort so
one failing channel never blocks the others.
"""

from __future__ import annotations

import json
import logging
import smtplib
from collections.abc import Iterable
from email.message import EmailMessage
from typing import Protocol, runtime_checkable
from urllib.request import Request, urlopen

_log = logging.getLogger(__name__)


@runtime_checkable
class AlertChannel(Protocol):
    def send(self, subject: str, body: str) -> None:
        """Deliver an alert (best-effort)."""


class WebhookChannel:
    """POSTs ``{subject, body}`` as JSON to a URL."""

    def __init__(self, url: str, timeout: float = 5.0) -> None:
        self._url = url
        self._timeout = timeout

    def send(self, subject: str, body: str) -> None:  # pragma: no cover
        data = json.dumps({"subject": subject, "body": body}).encode()
        req = Request(
            self._url, data=data, headers={"Content-Type": "application/json"}
        )
        with urlopen(req, timeout=self._timeout):  # noqa: S310
            pass


class EmailChannel:
    """Sends a plaintext email via SMTP."""

    def __init__(
        self,
        host: str,
        sender: str,
        recipient: str,
        port: int = 25,
        timeout: float = 10.0,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._recipient = recipient
        self._timeout = timeout

    def send(self, subject: str, body: str) -> None:  # pragma: no cover
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._sender
        msg["To"] = self._recipient
        msg.set_content(body)
        with smtplib.SMTP(
            self._host, self._port, timeout=self._timeout
        ) as smtp:
            smtp.send_message(msg)


def dispatch(channels: Iterable[AlertChannel], subject: str, body: str) -> int:
    """Send to every channel; return how many succeeded (best-effort)."""
    sent = 0
    for channel in channels:
        try:
            channel.send(subject, body)
            sent += 1
        except Exception:  # noqa: BLE001 - one bad channel must not block
            _log.exception("alert channel failed: %s", subject)
    return sent


def build_channel(cfg: object) -> AlertChannel | None:
    """Construct an alert channel from an ``AlertChannelConfig`` row."""
    from ecallisto_ng.api.settings import get_settings

    kind = getattr(cfg, "kind", "")
    url = getattr(cfg, "url", "")
    recipient = getattr(cfg, "recipient", "")
    if kind == "webhook" and url:
        return WebhookChannel(url)
    if kind == "email" and recipient:
        s = get_settings()
        if not s.smtp_host:
            return None
        return EmailChannel(s.smtp_host, s.smtp_from, recipient, s.smtp_port)
    return None


def enabled_channels(rows: Iterable[object]) -> list[AlertChannel]:
    """Build channels for the enabled config rows (skips unbuildable)."""
    out: list[AlertChannel] = []
    for row in rows:
        if getattr(row, "enabled", False):
            channel = build_channel(row)
            if channel is not None:
                out.append(channel)
    return out
