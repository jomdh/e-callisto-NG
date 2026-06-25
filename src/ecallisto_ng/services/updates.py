"""Update version reporting (DESIGN 15).

Version-compare helpers + the current version/channel. The actual
apply/rollback is a host operation run through a least-privilege hook
(packaging), not from the web process; this module owns the pure comparison
the UI uses to decide whether a newer build is available on the channel.
"""

from __future__ import annotations

from ecallisto_ng import __version__


def parse_version(v: str) -> tuple[int, ...]:
    return tuple(int(part) for part in v.split(".") if part.isdigit())


def is_newer(candidate: str, current: str) -> bool:
    """True if ``candidate`` is a strictly newer semver than ``current``."""
    return parse_version(candidate) > parse_version(current)


def update_info(channel: str) -> dict[str, str]:
    return {"version": __version__, "channel": channel}
