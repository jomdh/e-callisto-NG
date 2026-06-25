#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standalone hardware scanner for an e-Callisto NG station.

Run this on the station (e.g. a Raspberry Pi) to confirm a Callisto is
reachable over USB-serial and to list any SDRs, WITHOUT installing the full
suite. The only dependency is pyserial.

    git clone https://github.com/<owner>/callisto_legacy   # or git pull
    cd callisto_legacy
    python3 -m pip install --user pyserial                 # if not present
    python3 scripts/scan_devices.py            # list serial ports + USB SDRs
    python3 scripts/scan_devices.py --probe    # also try the handshake
    python3 scripts/scan_devices.py --port /dev/ttyUSB0 --probe   # one port

A Callisto answers the ``?`` status query with lines beginning ``$CRX:``; that
is what the probe looks for. Add yourself to the ``dialout`` group if opening a
port is denied: ``sudo usermod -aG dialout $USER`` then re-login.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

# USB VID:PID -> human label (SDRs we recognize on the bus).
KNOWN_SDR = {
    (0x04B4, 0x00F3): "Cypress FX3 (RX-888 MkII, DFU/bootloader)",
    (0x04B4, 0x00F1): "Cypress FX3 (RX-888 MkII)",
    (0x0BDA, 0x2838): "RTL2838 (RTL-SDR)",
    (0x0BDA, 0x2832): "RTL2832U (RTL-SDR)",
    (0x1D50, 0x60A1): "Airspy",
    (0x1D50, 0x6089): "HackRF One",
    (0x1DF7, 0x2500): "SDRplay RSP",
}
SERIAL_BRIDGES = {
    (0x067B, 0x2303): "Prolific PL2303",
    (0x0403, 0x6001): "FTDI FT232",
    (0x10C4, 0xEA60): "Silicon Labs CP2102",
}

CALLISTO_PROBE = b"\rS0\r?\r"
CALLISTO_MARK = "$CRX"
BAUD = 115200


def probe_callisto(device, timeout=1.5):
    """Open a serial port and try the Callisto handshake -> (ok, info)."""
    try:
        import serial
    except ImportError:
        return False, "pyserial not installed (pip install pyserial)"
    try:
        with serial.Serial(device, BAUD, timeout=timeout) as port:
            port.reset_input_buffer()
            port.write(CALLISTO_PROBE)
            port.flush()
            data = port.read(512).decode("ascii", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return False, "open failed: %s" % exc
    if CALLISTO_MARK in data:
        line = next(
            (ln for ln in data.splitlines() if CALLISTO_MARK in ln), ""
        )
        return True, line.strip() or "Callisto ($CRX response)"
    return False, "no $CRX response (%d bytes)" % len(data)


def list_serial_ports():
    try:
        from serial.tools import list_ports
    except ImportError:
        print("  ! pyserial not installed; run: pip install pyserial")
        return []
    return list(list_ports.comports())


def read_sys(path):
    try:
        with open(path, encoding="ascii", errors="replace") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def check_soapy_rx888():
    """Report whether SoapySDR can see an rx888 device (real backend check)."""
    try:
        import SoapySDR
    except ImportError:
        print("  SoapySDR not installed -> RX-888 runs SYNTHETIC")
        return
    try:
        devs = SoapySDR.Device.enumerate("driver=rx888")
    except Exception as exc:  # noqa: BLE001
        print("  SoapySDR present, enumerate failed: %s" % exc)
        return
    if devs:
        print("  RX-888 reachable via SoapySDR (driver=rx888) -> REAL")
        for d in devs:
            print("    %s" % dict(d))
    else:
        print(
            "  SoapySDR present but no driver=rx888 device "
            "(check firmware/SoapyRX888 module) -> SYNTHETIC"
        )


def list_usb_sdrs():
    out = []
    for vendor_path in glob.glob("/sys/bus/usb/devices/*/idVendor"):
        base = os.path.dirname(vendor_path)
        vid_s = read_sys(vendor_path)
        pid_s = read_sys(os.path.join(base, "idProduct"))
        if not vid_s or not pid_s:
            continue
        try:
            vid, pid = int(vid_s, 16), int(pid_s, 16)
        except ValueError:
            continue
        label = KNOWN_SDR.get((vid, pid))
        if label:
            product = read_sys(os.path.join(base, "product")) or label
            out.append((vid, pid, product, label))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Scan for Callisto / SDR devices."
    )
    ap.add_argument(
        "--probe",
        action="store_true",
        help="open serial ports and try the Callisto handshake",
    )
    ap.add_argument(
        "--port",
        default="",
        help="probe only this serial device (implies --probe)",
    )
    args = ap.parse_args(argv)
    probe = args.probe or bool(args.port)

    print("== Serial ports (Callisto link candidates) ==")
    ports = list_serial_ports()
    if args.port:
        ports = [p for p in ports if p.device == args.port]
        if not ports:
            print("  (no such port: %s)" % args.port)
    if not ports:
        print("  (none)")
    found_callisto = False
    for p in ports:
        ids = ""
        if p.vid is not None:
            ids = " [%04x:%04x]" % (p.vid, p.pid or 0)
        bridge = SERIAL_BRIDGES.get((p.vid or -1, p.pid or -1))
        tag = " <%s>" % bridge if bridge else ""
        print("  %s%s  %s%s" % (p.device, ids, p.description or "", tag))
        if probe:
            ok, info = probe_callisto(p.device)
            mark = "CALLISTO" if ok else "not Callisto"
            print("      probe: %s -- %s" % (mark, info))
            found_callisto = found_callisto or ok

    print("\n== RX-888 via SoapySDR ==")
    check_soapy_rx888()

    print("\n== USB SDRs (recognized) ==")
    sdrs = list_usb_sdrs()
    if not sdrs:
        print("  (none recognized; non-Linux hosts can't read /sys)")
    for vid, pid, product, label in sdrs:
        print("  usb:%04x:%04x  %s  <%s>" % (vid, pid, product, label))

    print(
        "\nSummary: %d serial port(s), %d known SDR(s)%s."
        % (
            len(ports),
            len(sdrs),
            ", Callisto confirmed" if found_callisto else "",
        )
    )
    if not probe:
        print("Re-run with --probe to confirm the Callisto handshake.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
