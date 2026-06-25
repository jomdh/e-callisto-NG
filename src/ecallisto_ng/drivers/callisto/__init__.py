# SPDX-License-Identifier: AGPL-3.0-or-later
"""Callisto serial driver -- class-1 heterodyne (ADC + dumb MCU).

The first instrument driver. It ports the legacy e-Callisto serial protocol
(reverse-engineered from the Windows and Linux host software) behind the
:class:`ecallisto_ng.core.InstrumentDriver` contract. All class-1 specifics
(serial command set, EEPROM channel programming, swept-ADC hex stream) live
here; nothing leaks into ``core``.
"""

from __future__ import annotations

from ecallisto_ng.drivers.callisto.driver import CallistoConfig, CallistoDriver
from ecallisto_ng.drivers.callisto.simulator import SimulatedCallisto

__all__ = ["CallistoConfig", "CallistoDriver", "SimulatedCallisto"]
