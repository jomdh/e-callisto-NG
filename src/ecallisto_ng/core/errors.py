# SPDX-License-Identifier: AGPL-3.0-or-later
"""Instrument fault taxonomy crossing the driver seam (ADR-0010).

A conformant ``InstrumentDriver`` translates every transport/hardware fault
into this hierarchy -- a raw serial/USB exception never crosses the seam -- and
never hangs: ``stream()`` either yields, self-heals, or raises
``FatalInstrumentError``.
"""

from __future__ import annotations


class InstrumentError(Exception):
    """Base for any instrument-originated fault crossing the driver seam."""


class RecoverableInstrumentError(InstrumentError):
    """A transient fault the driver did or can recover from internally.

    Mostly internal to a driver; a lifecycle call (connect/configure) MAY
    surface it to invite a cheap retry.
    """


class FatalInstrumentError(InstrumentError):
    """The driver cannot self-heal; the caller must tear it down and rebuild."""
