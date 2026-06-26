# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source azimuth/elevation track for observation planning (legacy `astro`).

Computes a source's az/el over a UTC day for the station's coordinates, via
astropy -- the Sun, Moon, planets, and the strong fixed radio sources the
legacy planner offered. Pure (no I/O); used by the planning panel (F8).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from datetime import date as date_type

import astropy.units as u
import numpy as np
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time

# Strong fixed radio sources (J2000), from the legacy planner.
_FIXED: dict[str, SkyCoord] = {
    "cas_a": SkyCoord("23h23m24s", "+58d48m54s"),
    "cyg_a": SkyCoord("19h59m28.3s", "+40d44m02s"),
    "tau_a": SkyCoord("05h34m31.9s", "+22d00m52s"),
    "vir_a": SkyCoord("12h30m49.4s", "+12d23m28s"),
    "sgr_a": SkyCoord("17h45m40s", "-29d00m28s"),
    "orion": SkyCoord("05h35m17s", "-05d23m28s"),
}
_PLANETS = {"mercury", "venus", "mars", "jupiter", "saturn", "moon"}

SOURCES = ["sun", *sorted(_PLANETS), *sorted(_FIXED)]


def _source_coord(
    source: str, times: Time, location: EarthLocation
) -> SkyCoord:
    if source == "sun":
        return get_sun(times)
    if source in _PLANETS:
        return get_body(source, times, location)
    return _FIXED[source]


def source_altitudes(
    lat_deg: float,
    lon_deg: float,
    alt_m: float,
    day: date_type,
    source: str,
    step_minutes: int = 10,
) -> list[tuple[datetime, float]]:
    """``(utc_datetime, el_deg)`` across the UTC day for a source.

    The shared ephemeris the scheduler's window engine and the planning plot
    both build on -- so 'where is the source today' has one implementation.
    """
    if source not in SOURCES:
        raise ValueError(f"unknown source: {source}")
    location = EarthLocation(
        lat=lat_deg * u.deg, lon=lon_deg * u.deg, height=alt_m * u.m
    )
    n = int(24 * 60 / step_minutes) + 1
    start_dt = datetime(day.year, day.month, day.day, tzinfo=UTC)
    dts = [start_dt + timedelta(minutes=step_minutes * i) for i in range(n)]
    times = Time(dts)
    frame = AltAz(obstime=times, location=location)
    coord = _source_coord(source, times, location)
    el = np.atleast_1d(coord.transform_to(frame).alt.deg)
    return [(d, float(e)) for d, e in zip(dts, el, strict=False)]


def source_track(
    lat_deg: float,
    lon_deg: float,
    alt_m: float,
    day: date_type,
    source: str,
    step_minutes: int = 30,
) -> list[tuple[float, float, float]]:
    """Return ``(ut_hour, az_deg, el_deg)`` across the UTC day for a source."""
    if source not in SOURCES:
        raise ValueError(f"unknown source: {source}")
    location = EarthLocation(
        lat=lat_deg * u.deg, lon=lon_deg * u.deg, height=alt_m * u.m
    )
    n = max(1, int(24 * 60 / step_minutes))
    start = Time(f"{day.isoformat()}T00:00:00")
    times = start + np.arange(n) * (step_minutes * u.min)
    frame = AltAz(obstime=times, location=location)
    altaz = _source_coord(source, times, location).transform_to(frame)
    az = np.atleast_1d(altaz.az.deg)
    el = np.atleast_1d(altaz.alt.deg)
    hours = (np.arange(n) * step_minutes) / 60.0
    return [
        (round(float(h), 3), round(float(a), 2), round(float(e), 2))
        for h, a, e in zip(hours, az, el, strict=False)
    ]
