# SPDX-License-Identifier: AGPL-3.0-or-later
"""Dynamic-DNS update helper (DESIGN 10).

Most stations are on a dynamic IP behind NAT. The operator gives an update
URL template containing ``{ip}``; the updater substitutes the public IP
and issues a GET. The URL build is pure/testable; the HTTP call is a thin
wrapper so an offline test never makes a request.
"""

from __future__ import annotations

from urllib.request import urlopen


def build_update_url(template: str, ip: str) -> str:
    """Substitute ``{ip}`` in the provider's update-URL template."""
    if "{ip}" not in template:
        raise ValueError("update URL template must contain {ip}")
    return template.replace("{ip}", ip)


def current_public_ip(
    service: str = "https://api.ipify.org", timeout: float = 5.0
) -> str:  # pragma: no cover - network
    with urlopen(service, timeout=timeout) as resp:  # noqa: S310
        return resp.read().decode().strip()


def update(template: str, ip: str, timeout: float = 5.0) -> int:
    """Issue the DDNS update; return the HTTP status."""  # pragma: no cover
    url = build_update_url(template, ip)
    with urlopen(url, timeout=timeout) as resp:  # noqa: S310
        return int(resp.status)
