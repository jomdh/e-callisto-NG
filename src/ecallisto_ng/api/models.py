# SPDX-License-Identifier: AGPL-3.0-or-later
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


class RecorderRuntime(SQLModel, table=True):
    """Persisted recorder run-state per instrument (ADR-0007 / F14).

    Written by whichever process owns the recording (web or the `acquire`
    daemon), read by the web app -- so the dashboard reflects acquisition state
    across the process boundary.
    """

    instrument_id: int = Field(primary_key=True)
    state: str = "idle"
    last_file: str | None = None
    # Operator intent for a free-run (manual / no-schedule) instrument: the
    # scheduler keeps the device recording while this is True. Record/Stop set
    # it; at daemon boot it is seeded from Instrument.start_on_boot.
    desired: bool = False
    updated_at: datetime = Field(default_factory=_utcnow)


class WizardState(SQLModel, table=True):
    """Resumable first-run wizard state (single row, DESIGN 9)."""

    id: int | None = Field(default=None, primary_key=True)
    step: int = 0
    data_json: str = "{}"  # accumulated answers across steps


class AuditEvent(SQLModel, table=True):
    """An append-only record of a security-sensitive action (ADR-0006)."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow, index=True)
    actor: str = "system"  # username or "system"
    action: str = Field(index=True)  # e.g. user.create, login.fail
    target: str = ""
    detail: str = ""


class Session(SQLModel, table=True):
    """A server-side session; the token lives in an HttpOnly cookie."""

    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime


class AlertChannelConfig(SQLModel, table=True):
    """A configured alert destination (DESIGN 14a)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    kind: str = "webhook"  # webhook / email
    url: str = ""  # webhook URL
    recipient: str = ""  # email recipient
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class PeerStation(SQLModel, table=True):
    """Another station this observatory oversees (fleet view, DESIGN 8)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    base_url: str  # e.g. https://stn2.obs.example
    token: str = ""  # the peer's fleet token
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class AccessSettings(SQLModel, table=True):
    """How the station is reached remotely (single row). DESIGN 10."""

    id: int | None = Field(default=None, primary_key=True)
    mode: str = "lan"  # lan / public / tunnel
    hostname: str = ""  # public-HTTPS / DDNS hostname
    tls_email: str = ""  # Let's Encrypt account email (public mode)
    ddns_update_url: str = ""  # template; {ip} is substituted
    tunnel_relay: str = ""  # outbound relay target (tunnel mode)
    updated_at: datetime = Field(default_factory=_utcnow)


class Station(SQLModel, table=True):
    """This host's identity (single row), and its observatory + location."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = "station"
    observatory: str = ""
    latitude_deg: float = 0.0  # +N / -S
    longitude_deg: float = 0.0  # +E / -W
    altitude_m: float = 0.0
    horizon_deg: float = 0.0  # local horizon elevation (planning overlay)
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
    # Program-switch parity: the frequency program to record with (None = a
    # plain ramp from the instrument's channel count).
    program_id: int | None = Field(
        default=None, foreign_key="frequencyprogram.id"
    )
    # Scheduled-overview parity (legacy scheduler.cfg mode 8): trigger an
    # overview sweep at this HH:MM (empty = none); guarded once per day.
    overview_at: str = ""
    last_overview_date: str = ""
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class CalibrationSet(SQLModel, table=True):
    """Named per-channel calibration coefficients (a, b, cf, Tb).

    ``coefficients_json`` is a JSON array of ``[a, b, cf, tb]`` rows. A single
    row is broadcast to all channels; otherwise the count must match.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    coefficients_json: str = "[]"
    created_at: datetime = Field(default_factory=_utcnow)


class FrequencyProgram(SQLModel, table=True):
    """A named frequency plan: a list of channel frequencies (MHz).

    ``frequencies_json`` stores the channel list as a JSON array of floats.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    frequencies_json: str = "[]"
    # Channel indices flagged as light curves (legacy frq-file ``,>0`` flag).
    light_curve_indices_json: str = "[]"
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
    unit: str = "raw"  # raw / sfu / kelvin (calibrated output, DESIGN 6b)
    output_mode: str = "standard"  # legacy / standard / custom (DESIGN 6a)
    # The instrument's frequency plan: a program defines the range + channel
    # list used by manual AND scheduled recording. None -> a 45+N MHz ramp.
    program_id: int | None = Field(
        default=None, foreign_key="frequencyprogram.id"
    )
    calibration_set_id: int | None = Field(
        default=None, foreign_key="calibrationset.id"
    )
    enabled: bool = True
    # Free-run (manual / no-schedule) survival: if True the acquire daemon
    # auto-records on boot and keeps recording until a human Stops; if False a
    # manual Record runs until Stop but does not survive a reboot.
    start_on_boot: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
