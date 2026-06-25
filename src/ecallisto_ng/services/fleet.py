# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observatory fleet aggregation: poll peer stations' health (DESIGN 8).

The aggregation is pure and takes an injected ``fetch`` so it is testable
without the network; the default fetch uses urllib against each peer's
``/api/v1/fleet/health`` endpoint.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

Fetch = Callable[[str, str], dict[str, Any] | None]


def default_fetch(
    base_url: str, token: str, timeout: float = 5.0
) -> dict[str, Any] | None:  # pragma: no cover - network
    url = f"{base_url.rstrip('/')}/api/v1/fleet/health?" + urlencode(
        {"token": token}
    )
    try:
        with urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return dict(json.loads(resp.read().decode()))
    except Exception:  # noqa: BLE001 - unreachable peer
        return None


def gather_fleet(
    peers: Iterable[Any], fetch: Fetch = default_fetch
) -> list[dict[str, Any]]:
    """Return one status row per enabled peer (reachable + its health)."""
    out: list[dict[str, Any]] = []
    for peer in peers:
        if not getattr(peer, "enabled", True):
            continue
        health = fetch(peer.base_url, peer.token)
        out.append(
            {
                "name": peer.name,
                "base_url": peer.base_url,
                "reachable": health is not None,
                "health": health,
            }
        )
    return out
