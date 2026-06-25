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

    # Standard sunrise/sunset altitude: -0.8333 deg (refraction + solar
    # semidiameter), matching legacy helio.cpp h0Sun (audit B3).
    h0 = -0.8333
    sunrise: datetime | None = None
    sunset: datetime | None = None
    for i in range(1, n):
        if sunrise is None and alt[i - 1] < h0 <= alt[i]:
            sunrise = dts[i]
        if alt[i - 1] >= h0 > alt[i]:
            sunset = dts[i]
    transit = dts[int(np.argmax(alt))]
    return SunEvents(sunrise=sunrise, transit=transit, sunset=sunset)


def sun_window(
    latitude_deg: float,
    longitude_deg: float,
    day: date_type,
    margin_minutes: int = 0,
    horizon_deg: float = 0.0,
) -> tuple[datetime, datetime] | None:
    """Recording window (start, stop) for sun-relative mode, or None.

    None means no daytime window (polar night). Polar day records all day.
    An elevated local horizon trims the window by ``horizon/15`` hours each
    side (legacy SchedulerGeni Sternzei.cpp:89, audit B2), in addition to the
    manual ``margin_minutes``.
    """
    events = sun_events(latitude_deg, longitude_deg, day)
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC)
    if events.sunrise is None and events.sunset is None:
        return None  # caller decides polar-day vs polar-night by altitude
    # horizon/15 hours -> horizon_deg*4 minutes.
    trim = margin_minutes + horizon_deg * 4.0
    start = (events.sunrise or midnight) + timedelta(minutes=trim)
    stop = (events.sunset or (midnight + timedelta(days=1))) - timedelta(
        minutes=trim
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


def _quantize_15(dt: datetime) -> datetime:
    """Snap a time to the nearest quarter hour (legacy Sternzei.cpp)."""
    minutes = dt.hour * 60 + dt.minute + round(dt.second / 60)
    q = round(minutes / 15) * 15
    base = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(minutes=q)


def generate_sun_scheduler_cfg(
    latitude_deg: float,
    longitude_deg: float,
    day: date_type,
    focus_code: int = 1,
    horizon_deg: float = 0.0,
    overview: bool = True,
) -> str:
    """Build a SchedulerGeni-style ``scheduler.cfg`` for a day (audit B6).

    Emits sunrise-start, transit-restart, and sunset-stop lines (focus +
    quarter-hour-snapped, horizon-trimmed), plus an optional sunset+0.5h
    monitoring overview (mode 8) -- matching legacy SchedulerGeni.
    """
    from ecallisto_ng.services.legacy_export import (
        ExportEntry,
        build_scheduler_cfg,
    )

    events = sun_events(latitude_deg, longitude_deg, day)
    if events.sunrise is None or events.sunset is None:
        return build_scheduler_cfg([])  # polar day/night -> header only
    trim = timedelta(minutes=horizon_deg * 4.0)  # horizon/15 h
    start = _quantize_15(events.sunrise + trim)
    transit = _quantize_15(events.transit)
    stop = _quantize_15(events.sunset - trim)
    entries = [
        ExportEntry(f"{start:%H:%M:%S}", focus_code, "3"),
        ExportEntry(f"{transit:%H:%M:%S}", focus_code, "3"),  # restart
        ExportEntry(f"{stop:%H:%M:%S}", focus_code, "0"),
    ]
    if overview:
        ovs = _quantize_15(events.sunset + timedelta(minutes=30))
        entries.append(ExportEntry(f"{ovs:%H:%M:%S}", focus_code, "8"))
    return build_scheduler_cfg(entries)
