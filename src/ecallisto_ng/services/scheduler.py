# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sun-relative scheduling.

Computes sunrise / transit / sunset for the station's coordinates with astropy
(no Emacs-calendar hack -- DESIGN 12) and derives the daily recording window.
The window decision (`is_recording_desired`) is pure and testable; a thin
service ticks it against the clock to start/stop recordings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import date as date_type

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, get_sun
from astropy.time import Time


@dataclass(frozen=True)
class SunEvents:
    sunrise: datetime | None  # None = polar day or night
    transit: datetime
    sunset: datetime | None


def sun_events(
    latitude_deg: float,
    longitude_deg: float,
    day: date_type,
    step_minutes: int = 10,
) -> SunEvents:
    """Sunrise/transit/sunset (UTC) for a location on ``day``."""
    loc = EarthLocation(lat=latitude_deg * u.deg, lon=longitude_deg * u.deg)
    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    n = int(24 * 60 / step_minutes) + 1
    dts = [start + timedelta(minutes=step_minutes * i) for i in range(n)]
    times = Time(dts)
    altaz = AltAz(obstime=times, location=loc)
    alt = np.asarray(get_sun(times).transform_to(altaz).alt.deg)

    sunrise: datetime | None = None
    sunset: datetime | None = None
    for i in range(1, n):
        if sunrise is None and alt[i - 1] < 0 <= alt[i]:
            sunrise = dts[i]
        if alt[i - 1] >= 0 > alt[i]:
            sunset = dts[i]
    transit = dts[int(np.argmax(alt))]
    return SunEvents(sunrise=sunrise, transit=transit, sunset=sunset)


def sun_window(
    latitude_deg: float,
    longitude_deg: float,
    day: date_type,
    margin_minutes: int = 0,
) -> tuple[datetime, datetime] | None:
    """Recording window (start, stop) for sun-relative mode, or None.

    None means no daytime window (polar night). Polar day records all day.
    """
    events = sun_events(latitude_deg, longitude_deg, day)
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC)
    if events.sunrise is None and events.sunset is None:
        return None  # caller decides polar-day vs polar-night by altitude
    start = (events.sunrise or midnight) + timedelta(minutes=margin_minutes)
    stop = (events.sunset or (midnight + timedelta(days=1))) - timedelta(
        minutes=margin_minutes
    )
    if stop <= start:
        return None
    return start, stop


def fixed_window(
    day: date_type, start_hhmm: str, stop_hhmm: str
) -> tuple[datetime, datetime] | None:
    """Fixed-time window for ``day`` from ``HH:MM`` strings (UTC)."""
    try:
        sh, sm = (int(x) for x in start_hhmm.split(":"))
        eh, em = (int(x) for x in stop_hhmm.split(":"))
    except (ValueError, AttributeError):
        return None
    start = datetime(day.year, day.month, day.day, sh, sm, tzinfo=UTC)
    stop = datetime(day.year, day.month, day.day, eh, em, tzinfo=UTC)
    if stop <= start:
        return None
    return start, stop


def is_recording_desired(
    window: tuple[datetime, datetime] | None, now: datetime
) -> bool:
    """True if ``now`` falls within the recording window."""
    if window is None:
        return False
    start, stop = window
    return start <= now < stop
