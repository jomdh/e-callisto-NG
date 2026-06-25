"""Pure-protocol tests -- the encoded legacy domain knowledge, verified."""

from __future__ import annotations

from ecallisto_ng.drivers.callisto import protocol as p


def test_detect_firmware() -> None:
    assert p.detect_firmware("$CRX:ChargePump=on") is p.FIRMWARE_15
    assert p.detect_firmware("$CRX:Debug=off") is p.FIRMWARE_17
    assert p.detect_firmware("$CRX:V1.8 / 25.43MHz") is p.FIRMWARE_18
    # audit A5: unrecognized -> legacy default profile, not None
    assert p.detect_firmware("garbage") is p.FIRMWARE_DEFAULT


def test_firmware_traits() -> None:
    assert p.FIRMWARE_15.bit_depth == 8
    assert p.FIRMWARE_18.bit_depth == 10
    assert p.FIRMWARE_18.if_init == 36.13


def test_band_for() -> None:
    assert p.band_for(100.0) == 1
    assert p.band_for(171.0) == 1  # audit A1: legacy <= -> boundary stays low
    assert p.band_for(300.0) == 2
    assert p.band_for(450.0) == 2  # boundary stays mid
    assert p.band_for(800.0) == 4


def test_divider_bytes_known_vector() -> None:
    # f=100, if_init=37.7 -> int(137.7/0.0625)=2203 -> hi=8, lo=155
    hi, lo = p.divider_bytes(100.0, 37.7)
    assert (hi, lo) == (8, 155)


def test_channel_command_format() -> None:
    cmd = p.channel_command(0, 100.0, p.FIRMWARE_15, chargepump=True)
    assert cmd == b"FE1,008,155,198,001\r"  # control 0x86|0x40 = 198
    cmd_no_cp = p.channel_command(0, 100.0, p.FIRMWARE_15, chargepump=False)
    assert cmd_no_cp == b"FE1,008,155,134,001\r"  # control 0x86 = 134


def test_channel_command_local_oscillator() -> None:
    # effective freq = |f - lo|, used for divider and band selection
    cmd = p.channel_command(4, 500.0, p.FIRMWARE_15, local_oscillator=400.0)
    assert cmd.startswith(b"FE5,")
    assert cmd.endswith(b",001\r")  # |500-400|=100 -> low band


def test_clock_command() -> None:
    assert p.clock_command(1, 800) == b"GS107\r"  # 86400//800 - 1
    assert p.clock_command(2, 1000) == b"GA499\r"  # 500000//1000 - 1
    assert p.clock_command(0, 800) is None  # software clock, no divider


def test_start_commands() -> None:
    assert p.start_commands(1, 64) == b"FS0100\rL64\rS1\rGE\r"
    assert p.start_commands(12, 200) == b"FS1211\rL200\rS1\rGE\r"


def test_to_8bit() -> None:
    assert p.to_8bit(1023, data10bit=True) == 255  # 10-bit -> 8-bit
    assert p.to_8bit(200, data10bit=False) == 200
