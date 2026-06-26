#!/bin/sh
# e-Callisto NG: keep the station awake -- disable WiFi power-save and USB
# autosuspend. Run at every boot by ecallisto-power.service (udev/NetworkManager
# settings alone did not survive a reboot on Ubuntu 24.04). Best-effort.
set -e 2>/dev/null || true
for w in /sys/class/net/wl*; do
    [ -e "$w" ] || continue
    iw dev "$(basename "$w")" set power_save off 2>/dev/null || true
done
for c in /sys/bus/usb/devices/*/power/control; do
    echo on > "$c" 2>/dev/null || true
done
exit 0
