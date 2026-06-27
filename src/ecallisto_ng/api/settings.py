# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typed application settings, loaded from the environment.

Read via ``pydantic-settings`` (never hardcode paths/secrets; CLAUDE rule).
Prefix ``ECALLISTO_``; a local ``.env`` is honored. Secrets stay out of code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Station-wide configuration."""

    model_config = SettingsConfigDict(
        env_prefix="ECALLISTO_", env_file=".env", extra="ignore"
    )

    data_dir: Path = Path("/var/lib/callisto")
    config_dir: Path = Path("/etc/callisto")
    db_url: str = "sqlite:///./ecallisto.db"
    bind: str = "127.0.0.1"
    port: int = 8000
    # Server-side session signing; overridden in production via env.
    secret_key: str = "dev-insecure-change-me"
    # Background loop tick intervals (seconds); 0 disables (used in tests).
    # The scheduler also enacts operator Record/Stop (via the desired flag), so
    # keep it short enough to feel responsive.
    scheduler_tick_seconds: int = 5
    uploader_tick_seconds: int = 60
    # Localhost UDP port bridging live frames from the acquire daemon to the
    # web app's WebSocket feed (two-process mode); same-host only.
    live_bridge_port: int = 8799
    # Days to keep uploaded local files; <0 disables pruning.
    retention_days: int = -1
    # If set, uploaded files are moved into this dated YYYY/MM/DD archive
    # (legacy FITbackup) instead of being pruned by retention.
    archive_dir: str = ""
    # Block recording when the clock is known-unsynced (DESIGN 12a).
    require_clock_sync: bool = False
    # Max tolerated clock offset (ms) before drift-gating pauses (0 = off).
    max_clock_offset_ms: float = 0.0
    # Run the scheduler/uploader loops inside the web process. Set false when
    # the `ecallisto-ng acquire` daemon owns them (ADR-0007).
    run_loops_in_web: bool = True
    # Shared token that lets an observatory poll this station's fleet health.
    # Empty disables the fleet-health endpoint.
    fleet_token: str = ""
    # SMTP for the email alert channel (DESIGN 14a).
    smtp_host: str = ""
    smtp_port: int = 25
    smtp_from: str = "ecallisto@localhost"
    # Update channel the station tracks (DESIGN 15).
    update_channel: str = "stable"
    # Active time source: "system" (OS clock + chrony) or "gps" (ADR-0009).
    time_source: str = "system"
    # Least-privilege host-action hook command (ADR-0008); empty = disabled.
    host_hook: str = ""
    # Log file the System log viewer tails (read-only).
    log_file: str = ""
    # Automated remote recovery (ADR-0012): when a recording instrument goes
    # STALLED past self-heal, the acquire watchdog invokes the host hook to
    # power-cycle it. Opt-in (needs host_hook + sudoers); bounded by the budget
    # below so it alerts instead of looping power-cycles forever.
    auto_recover: bool = False
    # Engine-level stall bound = max(this, stall_sweeps / sweep_rate). Longer
    # than the driver's own no-data timeout so the driver self-heals first.
    stall_grace_seconds: float = 90.0
    # Max automated recoveries per instrument per window, then alert + stop.
    auto_recover_budget: int = 3
    auto_recover_window_seconds: float = 3600.0


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton."""
    return Settings()
