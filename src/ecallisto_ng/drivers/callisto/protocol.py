# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pure Callisto serial-protocol logic -- no I/O.

Every value here is reverse-engineered from the legacy host software (the
Linux daemon ``eeprom.c``/``callisto.c`` and the Windows ``EEPROM.cpp``/
``RXRS232.cpp``). Keeping it pure makes the protocol exhaustively testable
against known vectors, independent of any serial port.

Wire framing (class-1):
- Text messages are ``$ ... \\r`` framed.
- Hex data transmission starts with STX (0x02), is a stream of ASCII hex
  digits (4 per sample), and ends with ``&``. The sample value ``0x2323``
  ("2323") is the transmission end marker.
- ``]`` is the EEPROM-write acknowledge.
"""

from __future__ import annotations

from dataclasses import dataclass

# Tuner synthesizer step (MHz) and band edges (MHz).
SYNTHESIZER_RESOLUTION = 0.0625
LOW_BAND = 171.0
MID_BAND = 450.0

# Control-byte bits (CD1316-class tuner).
_CONTROL_BASE = 0x86
_CONTROL_CHARGEPUMP = 0x40

# Framing bytes.
MESSAGE_START = b"$"
MESSAGE_END = b"\r"
DATA_START = b"\x02"  # STX
DATA_END = b"&"
EEPROM_READY = b"]"
END_MARKER = 0x2323  # a 4-hex-digit sample equal to this ends transmission

# Fixed command strings.
RESET = b"D0\rGD\rS0\r"
ID_QUERY = b"S0\r"
ID_RESPONSE = b"$CRX:Stopped\r"
STATUS_QUERY = b"?\r"
OVERVIEW = b"T0\rM2\r%5\rF0045.0\rL13200\rP2\r"


@dataclass(frozen=True)
class Firmware:
    """Host-relevant firmware traits, derived from the ``?`` response."""

    version: str
    if_init: float  # IF #1 + LO frequency (MHz)
    data10bit: bool  # 10-bit samples (1.7/1.8) vs 8-bit (1.5)
    eeprom_info: bool  # FR response carries an extra EEPROM info line

    @property
    def bit_depth(self) -> int:
        return 10 if self.data10bit else 8


# Default = firmware 1.5 (LO 27 MHz, 8-bit), matching the legacy default.
FIRMWARE_15 = Firmware("1.5", if_init=37.7, data10bit=False, eeprom_info=False)
FIRMWARE_17 = Firmware("1.7", if_init=37.7, data10bit=True, eeprom_info=False)
FIRMWARE_18 = Firmware("1.8", if_init=36.13, data10bit=True, eeprom_info=True)


def detect_firmware(first_status_line: str) -> Firmware | None:
    """Map the first line of the ``?`` response to a firmware profile.

    Returns ``None`` for an unrecognized (unsupported) device.
    """
    line = first_status_line
    if line.startswith("$CRX:ChargePump="):
        return FIRMWARE_15
    if line.startswith("$CRX:Debug="):
        return FIRMWARE_17
    if line.startswith("$CRX:V1.8 / "):
        return FIRMWARE_18
    return None


def band_for(freq_mhz: float) -> int:
    """Band-select byte for a tuner frequency (1=low, 2=mid, 4=high)."""
    if freq_mhz < LOW_BAND:
        return 1
    if freq_mhz < MID_BAND:
        return 2
    return 4


def divider_bytes(freq_mhz: float, if_init: float) -> tuple[int, int]:
    """PLL divider high/low bytes for a tuner frequency."""
    divider = int((freq_mhz + if_init) / SYNTHESIZER_RESOLUTION)
    return (divider >> 8) & 0xFF, divider & 0xFF


def channel_command(
    index: int,
    freq_mhz: float,
    firmware: Firmware,
    *,
    local_oscillator: float = 0.0,
    chargepump: bool = True,
) -> bytes:
    """Build the ``FE`` EEPROM-write command for one channel.

    ``index`` is 0-based here; the wire command is 1-based. ``freq_mhz`` is the
    requested RF; the effective tuner frequency is corrected for an external
    local oscillator (``|f - lo|``), as in the legacy code.
    """
    effective = abs(freq_mhz - local_oscillator)
    div_hi, div_lo = divider_bytes(effective, firmware.if_init)
    control = _CONTROL_BASE | (_CONTROL_CHARGEPUMP if chargepump else 0)
    band = band_for(effective)
    return (
        f"FE{index + 1},{div_hi:03d},{div_lo:03d},"
        f"{control:03d},{band:03d}\r"
    ).encode("ascii")


def clock_command(clocksource: int, sample_rate_hz: int) -> bytes | None:
    """Counter-divider command for the selected clock source.

    Source 1 = internal (11.0592 MHz), 2 = external (1 MHz). Source 0
    (software) needs no divider command.
    """
    rate = max(sample_rate_hz, 1)
    if clocksource == 1:
        return f"GS{86400 // rate - 1}\r".encode("ascii")
    if clocksource == 2:
        return f"GA{500000 // rate - 1}\r".encode("ascii")
    return None


def init_commands(
    clocksource: int,
    sample_rate_hz: int,
    agclevel: int,
    chargepump: bool,
) -> list[bytes]:
    """Pre-acquisition setup: clock divider, then T/O/C."""
    cmds: list[bytes] = []
    clk = clock_command(clocksource, sample_rate_hz)
    if clk is not None:
        cmds.append(clk)
    cmds.append(
        f"T{clocksource}\rO{agclevel:03d}\rC{int(chargepump)}\r".encode(
            "ascii"
        )
    )
    return cmds


def start_commands(focuscode: int, nchannels: int) -> bytes:
    """Set focus code, sweep length, start the state machine, enable data."""
    return (
        f"FS{focuscode:02d}{focuscode - 1:02d}\r" f"L{nchannels}\rS1\rGE\r"
    ).encode("ascii")


STOP = b"GD\r"
HALT = b"S0\r"
DETECTOR_QUERY = b"A0\r"  # read detector voltage (bench)


def tune_command(frequency_mhz: float) -> bytes:
    """Tune the receiver to one frequency (legacy ``F0``)."""
    return f"F0{frequency_mhz:.1f}\r".encode("ascii")


def gain_command(pwm: int) -> bytes:
    """Set the AGC/PWM gain 0-255 (legacy ``O``)."""
    return f"O{max(0, min(255, pwm)):03d}\r".encode("ascii")


def relay_command(code: int) -> bytes:
    """Switch the focus/relay tree to a 6-bit code (legacy ``fs``)."""
    return f"fs{code & 0x3F:02d}\r".encode("ascii")


def parse_detector(text: str) -> float | None:
    """Parse a ``$CRX:ADC0=<mV>`` detector reply; mV or None."""
    marker = "ADC0="
    idx = text.find(marker)
    if idx < 0:
        return None
    tail = text[idx + len(marker) :].strip()
    digits = ""
    for ch in tail:
        if ch.isdigit() or ch in ".-":
            digits += ch
        else:
            break
    try:
        return float(digits)
    except ValueError:
        return None


def to_8bit(value: int, data10bit: bool) -> int:
    """Normalize a raw sample to 8 bits (10-bit devices are right-shifted)."""
    return (value >> 2) if data10bit else (value & 0xFF)
