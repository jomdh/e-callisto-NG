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


class UploadTarget(SQLModel, table=True):
    """Where finished files are sent, and when.

    ``protocol`` = local / ftp. ``dispatch`` = immediate / scheduled / manual.
    Credentials are stored here; encrypting them at rest is tracked as B2.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    protocol: str = "local"
    host: str = ""  # ftp host, or destination dir for local
    base_path: str = "/"
    username: str = ""
    password: str = ""
    dispatch: str = "manual"  # immediate / scheduled / manual
    window_start: str = "00:00"  # scheduled-dispatch window (UTC HH:MM)
    window_stop: str = "23:59"
    gzip: bool = True
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class UploadJob(SQLModel, table=True):
    """Tracks whether a file has been uploaded to a target."""

    id: int | None = Field(default=None, primary_key=True)
    target_id: int = Field(foreign_key="uploadtarget.id", index=True)
    filename: str = Field(index=True)
    state: str = "done"  # done / error
    error: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


class Schedule(SQLModel, table=True):
    """A recording schedule for one instrument.

    ``kind`` = ``sun`` (sunrise->sunset, station coordinates) or ``fixed``
    (``start_utc``/``stop_utc`` HH:MM). ``margin_minutes`` trims a sun window.
    """

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instrument.id", index=True)
    kind: str = "sun"
    margin_minutes: int = 0
    start_utc: str = "00:00"  # fixed mode
    stop_utc: str = "23:59"  # fixed mode
    enabled: bool = True
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
    file_seconds: int = 900  # length of one recording/FITS file
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
