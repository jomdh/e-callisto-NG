"""Generate a Caddyfile for the chosen remote-access mode (DESIGN 10).

Pure string generation -- the operator/installer writes the result and runs
Caddy. Three modes:
- ``lan``: front the app on :443 with a self-signed cert (``tls internal``).
- ``public``: serve at ``hostname`` with auto Let's Encrypt (``tls_email``).
- ``tunnel``: the app is bound locally and reached via an outbound relay;
  Caddy is not needed, so a documented stub is emitted.
"""

from __future__ import annotations


def build_caddyfile(
    mode: str, hostname: str, app_port: int, tls_email: str
) -> str:
    upstream = f"reverse_proxy 127.0.0.1:{app_port}"
    if mode == "public":
        if not hostname:
            raise ValueError("public mode requires a hostname")
        header = f"{{\n\temail {tls_email}\n}}\n\n" if tls_email else ""
        return f"{header}{hostname} {{\n\t{upstream}\n}}\n"
    if mode == "lan":
        return f":443 {{\n\ttls internal\n\t{upstream}\n}}\n"
    if mode == "tunnel":
        return (
            "# tunnel mode: the app is reached through an outbound relay\n"
            f"# ({hostname or 'relay target configured separately'}).\n"
            "# Caddy is not required on the station.\n"
        )
    raise ValueError(f"unknown access mode: {mode}")
