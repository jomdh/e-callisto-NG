# SPDX-License-Identifier: AGPL-3.0-or-later
"""Instrument fault taxonomy (ADR-0010)."""

from __future__ import annotations

from ecallisto_ng.core import (
    CONTRACT_VERSION,
    FatalInstrumentError,
    InstrumentError,
    RecoverableInstrumentError,
)


def test_taxonomy_hierarchy() -> None:
    assert issubclass(RecoverableInstrumentError, InstrumentError)
    assert issubclass(FatalInstrumentError, InstrumentError)
    assert not issubclass(FatalInstrumentError, RecoverableInstrumentError)
    # catchable as the base
    try:
        raise FatalInstrumentError("dead port")
    except InstrumentError as exc:
        assert str(exc) == "dead port"


def test_contract_version_bumped() -> None:
    assert CONTRACT_VERSION == "0.5.0"  # ADR-0010
