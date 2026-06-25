# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolve an instrument's channel list from its frequency plan (M32).

Precedence: an explicit override (a schedule's program) > the instrument's own
program > a plain ``45 + N`` MHz ramp from the channel count. A program carries
the channel frequencies and per-channel light-curve flags. This one resolver
is used by both manual record and the scheduler, so the range an operator
defines is what actually gets recorded everywhere.
"""

from __future__ import annotations

import json

from sqlmodel import Session

from ecallisto_ng.api.models import FrequencyProgram, Instrument
from ecallisto_ng.core.spectra import Channel


def _program_channels(
    db: Session, program_id: int | None
) -> list[Channel] | None:
    if program_id is None:
        return None
    prog = db.get(FrequencyProgram, program_id)
    if prog is None:
        return None
    freqs = json.loads(prog.frequencies_json)
    if not freqs:
        return None
    lc = set(json.loads(prog.light_curve_indices_json))
    return [
        Channel(frequency_mhz=float(f), light_curve=(i in lc))
        for i, f in enumerate(freqs)
    ]


def resolve_channels(
    db: Session, inst: Instrument, program_id: int | None = None
) -> list[Channel]:
    """Channels for a recording: override program > instrument program > ramp.

    ``program_id`` is an explicit override (e.g. a schedule's program). When it
    or the instrument's ``program_id`` resolves to a non-empty program, those
    frequencies are used; otherwise a plain ``45 + i`` MHz ramp.
    """
    for pid in (program_id, inst.program_id):
        chans = _program_channels(db, pid)
        if chans:
            return chans
    return [Channel(frequency_mhz=45.0 + i) for i in range(inst.channels)]
