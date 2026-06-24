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


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton."""
    return Settings()
