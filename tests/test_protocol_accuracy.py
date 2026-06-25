# SPDX-License-Identifier: AGPL-3.0-or-later
"""Byte-exact protocol accuracy fixes vs Borland callisto.exe (M26 A1-A5)."""

from __future__ import annotations

from ecallisto_ng.drivers.callisto import protocol as p


def test_band_boundaries_inclusive() -> None:  # audit A1
    assert p.band_for(170.9) == 1
    assert p.band_for(171.0) == 1  # legacy <= : exactly 171 -> band 1
    assert p.band_for(171.1) == 2
    assert p.band_for(450.0) == 2  # exactly 450 -> band 2
    assert p.band_for(450.1) == 4


def test_tune_command_format() -> None:  # audit A2 / C1
    assert p.tune_command(45.0) == b"F0045.000\r"  # zero-pad width 7, 3 dp
    assert p.tune_command(150.125) == b"F0150.125\r"  # sub-0.1 MHz preserved
    assert p.tune_command(870.0) == b"F0870.000\r"


def test_ten_bit_forces_chargepump() -> None:  # audit A4
    # 10-bit firmware (1.8) forces control byte 0xC6 even with chargepump=False
    cmd10 = p.channel_command(
        0, 100.0, p.FIRMWARE_18, chargepump=False
    ).decode()
    assert cmd10.split(",")[3] == "198"  # 0xC6 = 198
    # 8-bit firmware honors the flag
    cmd8_off = p.channel_command(
        0, 100.0, p.FIRMWARE_15, chargepump=False
    ).decode()
    assert cmd8_off.split(",")[3] == "134"  # 0x86 = 134
    cmd8_on = p.channel_command(
        0, 100.0, p.FIRMWARE_15, chargepump=True
    ).decode()
    assert cmd8_on.split(",")[3] == "198"  # 0xC6 = 198


def test_firmware_detection_and_default() -> None:  # audit A5
    assert p.detect_firmware("$CRX:ChargePump=1").version == "1.5"
    assert p.detect_firmware("$CRX:V1.8 / 25.43MHz").version == "1.8"
    # unrecognized -> default profile (10-bit, 27 MHz / if_init 37.70)
    fw = p.detect_firmware("$CRX:something unexpected")
    assert fw.version == "default"
    assert fw.data10bit is True
    assert fw.if_init == 37.7


def test_divider_math_unchanged() -> None:  # audit A11 (regression guard)
    # 100 MHz + if_init 37.7 = 137.7 / 0.0625 = 2203 -> hi 8, lo 155
    hi, lo = p.divider_bytes(100.0, 37.7)
    assert hi == (2203 >> 8) & 0xFF
    assert lo == 2203 & 0xFF
