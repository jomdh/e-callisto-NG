"""Instrument drivers -- one concrete implementation per instrument type.

Each driver implements the :class:`ecallisto_ng.core.InstrumentDriver`
contract and declares its :class:`~ecallisto_ng.core.Capabilities`. The
Callisto serial driver is the first; ``fake`` is a hardware-free driver used
for development and CI.
"""
