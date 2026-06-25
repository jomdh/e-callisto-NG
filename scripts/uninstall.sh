#!/usr/bin/env bash
# Remove the e-Callisto NG station services + udev rules (run with sudo).
# Leaves the checkout, venv, .env, and data untouched.
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then echo "run with sudo"; exit 1; fi
echo "==> stopping + disabling services"
systemctl disable --now ecallisto-web ecallisto-acquire 2>/dev/null || true
rm -f /etc/systemd/system/ecallisto-web.service \
      /etc/systemd/system/ecallisto-acquire.service
systemctl daemon-reload
echo "==> removing udev rules"
rm -f /etc/udev/rules.d/99-ecallisto.rules
udevadm control --reload 2>/dev/null || true
echo "==> done (checkout/venv/.env/data left in place)."
