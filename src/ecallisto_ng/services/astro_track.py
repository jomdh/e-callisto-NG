"""Source azimuth/elevation track for observation planning (legacy `astro`).

Computes a source's az/el over a UTC day for the station's coordinates, via
astropy -- the Sun, Moon, planets, and the strong fixed radio sources the
legacy planner offered. Pure (no I/O); used by the planning panel (F8).
"""

from __future__ import annotations

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

    if source == "sun":
        coord = get_sun(times)
    elif source in _PLANETS:
        coord = get_body(source, times, location)
    else:
        coord = _FIXED[source]

    altaz = coord.transform_to(frame)
    az = np.atleast_1d(altaz.az.deg)
    el = np.atleast_1d(altaz.alt.deg)
    hours = (np.arange(n) * step_minutes) / 60.0
    return [
        (round(float(h), 3), round(float(a), 2), round(float(e), 2))
        for h, a, e in zip(hours, az, el, strict=False)
    ]
