"""Persistent models (SQLModel tables).

Importing this module registers the tables on ``SQLModel.metadata`` so
``init_db`` creates them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    """Access roles, ordered viewer < operator < admin."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


_ORDER = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}


def role_satisfies(have: Role, need: Role) -> bool:
    """True if ``have`` meets or exceeds ``need``."""
    return _ORDER[have] >= _ORDER[need]


class User(SQLModel, table=True):
    """A login account."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: Role = Role.VIEWER
    active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class Session(SQLModel, table=True):
    """A server-side session; the token lives in an HttpOnly cookie."""

    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime


class Station(SQLModel, table=True):
    """This host's identity (single row), and its observatory + location."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = "station"
    observatory: str = ""
    latitude_deg: float = 0.0  # +N / -S
    longitude_deg: float = 0.0  # +E / -W
    altitude_m: float = 0.0
    created_at: datetime = Field(default_factory=_utcnow)


class FrequencyProgram(SQLModel, table=True):
    """A named frequency plan: a list of channel frequencies (MHz).

    ``frequencies_json`` stores the channel list as a JSON array of floats.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    frequencies_json: str = "[]"
    start_mhz: float = 45.0
    stop_mhz: float = 870.0
    source: str = "manual"  # manual / generated
    created_at: datetime = Field(default_factory=_utcnow)


class Instrument(SQLModel, table=True):
    """A receiver controlled by this station."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    instrument_class: str = "heterodyne"  # heterodyne / sdr_soft / sdr_fpga
    address: str = ""  # serial path / USB id / host:port; empty -> fake
    focus_code: int = 1
    gain: int = 120
    channels: int = 200
    sweep_rate_hz: float = 4.0
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
