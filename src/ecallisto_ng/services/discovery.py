# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hardware discovery: scan USB-serial + USB for instruments (DESIGN 5a).

Enumerates serial ports (the heterodyne Callisto link) and USB devices (SDRs),
classifies each, and -- on request -- probes a serial port for the Callisto
handshake. Pure read-only; degrades to an empty result where the OS lacks the
relevant interfaces (e.g. ``/sys`` on non-Linux), so it is safe to call
anywhere. Maps a found device to a suggested instrument class + address.
"""

from __future__ import annotations

import glob
import logging
import os
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)

# USB VID:PID -> (label, suggested instrument class). SDRs first, then the
# USB-serial bridges that typically carry a Callisto (confirmed by probing).
_KNOWN_SDR: dict[tuple[int, int], str] = {
    (0x04B4, 0x00F3): "Cypress FX3 (RX-888 MkII, DFU/bootloader)",
    (0x04B4, 0x00F1): "Cypress FX3 (RX-888 MkII)",
    (0x0BDA, 0x2838): "RTL2838 (RTL-SDR)",
    (0x0BDA, 0x2832): "RTL2832U (RTL-SDR)",
    (0x1D50, 0x60A1): "Airspy",
    (0x1D50, 0x6089): "HackRF One",
    (0x1DF7, 0x2500): "SDRplay RSP",
}
_SERIAL_BRIDGES: dict[tuple[int, int], str] = {
    (0x067B, 0x2303): "Prolific PL2303",
    (0x0403, 0x6001): "FTDI FT232",
    (0x10C4, 0xEA60): "Silicon Labs CP2102",
}

# Callisto serial handshake (RXRS232.cpp): stop, then status query.
_CALLISTO_PROBE = b"\rS0\r?\r"
_CALLISTO_MARK = "$CRX"
_BAUD = 115200


@dataclass(frozen=True)
class DiscoveredDevice:
    """One candidate instrument found on the host."""

    address: str  # serial path or usb:VID:PID
    kind: str  # serial | usb
    description: str
    vid: int | None
    pid: int | None
    suggested_class: str  # heterodyne | sdr_soft | unknown
    callisto: bool  # confirmed Callisto handshake (serial probe only)
    detail: str  # firmware/status line, or the matched label

    def as_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["vid"] = f"{self.vid:04x}" if self.vid is not None else None
        d["pid"] = f"{self.pid:04x}" if self.pid is not None else None
        return d


def probe_callisto(device: str, timeout: float = 1.5) -> tuple[bool, str]:
    """Open a serial port and try the Callisto handshake.

    Returns ``(is_callisto, info)`` where ``info`` is the first ``$CRX`` line
    (firmware/status) or an error message. Never raises.
    """
    try:
        import serial  # pyserial; lazy so a missing dep degrades gracefully
    except ImportError:  # pragma: no cover - pyserial is a dependency
        return False, "pyserial not installed"
    try:
        with serial.Serial(device, _BAUD, timeout=timeout) as port:
            port.reset_input_buffer()
            port.write(_CALLISTO_PROBE)
            port.flush()
            data = port.read(512).decode("ascii", errors="replace")
    except Exception as exc:  # noqa: BLE001 - report, never crash the scan
        return False, f"open failed: {exc}"
    if _CALLISTO_MARK in data:
        line = next(
            (ln for ln in data.splitlines() if _CALLISTO_MARK in ln), ""
        )
        return True, line.strip()
    return False, "no $CRX response"


def scan_serial_ports(probe: bool = False) -> list[DiscoveredDevice]:
    """Serial ports as candidate Callisto links (optionally probed)."""
    try:
        from serial.tools import list_ports
    except ImportError:  # pragma: no cover
        return []
    found: list[DiscoveredDevice] = []
    for p in list_ports.comports():
        vid, pid = p.vid, p.pid
        bridge = _SERIAL_BRIDGES.get((vid or -1, pid or -1))
        is_callisto, detail = False, bridge or (p.description or "serial port")
        if probe:
            is_callisto, info = probe_callisto(p.device)
            if is_callisto:
                detail = info
        suggested = "heterodyne" if (is_callisto or bridge) else "unknown"
        found.append(
            DiscoveredDevice(
                address=p.device,
                kind="serial",
                description=p.description or p.device,
                vid=vid,
                pid=pid,
                suggested_class=suggested,
                callisto=is_callisto,
                detail=detail,
            )
        )
    return found


def _read_sys(path: str) -> str:
    try:
        with open(path, encoding="ascii", errors="replace") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def scan_usb_devices() -> list[DiscoveredDevice]:
    """USB devices matched against the known-SDR table (Linux ``/sys``)."""
    found: list[DiscoveredDevice] = []
    for vendor_path in glob.glob("/sys/bus/usb/devices/*/idVendor"):
        base = os.path.dirname(vendor_path)
        vid_s = _read_sys(vendor_path)
        pid_s = _read_sys(os.path.join(base, "idProduct"))
        if not vid_s or not pid_s:
            continue
        try:
            vid, pid = int(vid_s, 16), int(pid_s, 16)
        except ValueError:
            continue
        label = _KNOWN_SDR.get((vid, pid))
        if label is None:
            continue  # only surface recognized SDRs from the USB sweep
        product = _read_sys(os.path.join(base, "product")) or label
        found.append(
            DiscoveredDevice(
                address=f"usb:{vid:04x}:{pid:04x}",
                kind="usb",
                description=product,
                vid=vid,
                pid=pid,
                suggested_class="sdr_soft",
                callisto=False,
                detail=label,
            )
        )
    return found


def discover(probe: bool = False) -> list[DiscoveredDevice]:
    """All candidate instruments on this host (serial + USB)."""
    devices = scan_serial_ports(probe) + scan_usb_devices()
    logger.info("hardware scan found %d device(s)", len(devices))
    return devices
