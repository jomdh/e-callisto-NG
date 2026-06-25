#!/usr/bin/env bash
# e-Callisto NG station installer.
#
#   sudo ./scripts/install.sh
#
# First run prepares the OS environment (apt packages, dialout/plugdev groups,
# udev rules, ModemManager carve-out), installs the suite into a venv, writes
# .env, and registers + starts two systemd services (web + acquire). Idempotent
# -- safe to re-run after a `git pull`. See DEPLOYMENT.md for the full rationale.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo (it installs packages + systemd units): sudo $0" >&2
    exit 1
fi

# The unprivileged account the station runs as: the sudo invoker, else 'pi'.
RUN_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
VENV="$APP_DIR/.venv"
ENV_FILE="$APP_DIR/.env"
as_user() { sudo -u "$RUN_USER" "$@"; }

echo "==> Station install: user=$RUN_USER  dir=$APP_DIR"

# --- 1. system packages --------------------------------------------------
PYV="$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "==> apt packages (python$PYV-venv, pip, chrony, usbutils, build tools)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq || true
apt-get install -y --no-install-recommends \
    "python${PYV}-venv" python3-pip python3-dev build-essential \
    git chrony usbutils 2>/dev/null || \
    apt-get install -y --no-install-recommends \
        python3-venv python3-pip git chrony usbutils || true
systemctl enable --now chrony 2>/dev/null || true

# --- 2. groups: serial (dialout) + USB SDR (plugdev) ---------------------
echo "==> adding $RUN_USER to dialout + plugdev"
getent group plugdev >/dev/null || groupadd plugdev
usermod -aG dialout,plugdev "$RUN_USER"

# --- 3. udev rules: ModemManager carve-out + SDR access ------------------
echo "==> installing udev rules"
install -m 0644 packaging/udev/99-ecallisto.rules \
    /etc/udev/rules.d/99-ecallisto.rules
udevadm control --reload 2>/dev/null || true
udevadm trigger 2>/dev/null || true

# --- 4. virtualenv + suite (system-site-packages for SoapySDR) -----------
if [ ! -x "$VENV/bin/python" ]; then
    echo "==> creating venv (--system-site-packages, for SoapySDR/RX-888)"
    as_user python3 -m venv --system-site-packages "$VENV"
fi
echo "==> installing the suite"
as_user "$VENV/bin/pip" install -q --upgrade pip
as_user "$VENV/bin/pip" install -q -e "$APP_DIR"

# --- 5. .env: secret, data dir, acquire-owns-loops -----------------------
if [ ! -f "$ENV_FILE" ]; then
    echo "==> writing .env (generated secret; acquire owns the loops)"
    as_user cp "$APP_DIR/.env.example" "$ENV_FILE"
    KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
    as_user sed -i \
        -e "s|^ECALLISTO_SECRET_KEY=.*|ECALLISTO_SECRET_KEY=$KEY|" \
        -e "s|^ECALLISTO_DATA_DIR=.*|ECALLISTO_DATA_DIR=$APP_DIR/data|" \
        "$ENV_FILE"
fi
grep -q '^ECALLISTO_RUN_LOOPS_IN_WEB=' "$ENV_FILE" \
    && as_user sed -i 's|^ECALLISTO_RUN_LOOPS_IN_WEB=.*|ECALLISTO_RUN_LOOPS_IN_WEB=false|' "$ENV_FILE" \
    || as_user bash -c "echo 'ECALLISTO_RUN_LOOPS_IN_WEB=false' >> '$ENV_FILE'"
as_user mkdir -p "$APP_DIR/data"

BIND="$(grep -E '^ECALLISTO_BIND=' "$ENV_FILE" | cut -d= -f2)"; BIND="${BIND:-0.0.0.0}"
PORT="$(grep -E '^ECALLISTO_PORT=' "$ENV_FILE" | cut -d= -f2)"; PORT="${PORT:-8000}"

# --- 6. systemd services: web + acquire ----------------------------------
echo "==> installing systemd units (ecallisto-web + ecallisto-acquire)"
render() {
    sed -e "s|@USER@|$RUN_USER|g" -e "s|@APP_DIR@|$APP_DIR|g" \
        -e "s|@VENV@|$VENV|g" -e "s|@ENV_FILE@|$ENV_FILE|g" \
        -e "s|@BIND@|$BIND|g" -e "s|@PORT@|$PORT|g" "$1"
}
render packaging/systemd/ecallisto-web.service.in \
    > /etc/systemd/system/ecallisto-web.service
render packaging/systemd/ecallisto-acquire.service.in \
    > /etc/systemd/system/ecallisto-acquire.service
systemctl daemon-reload
systemctl enable --now ecallisto-web ecallisto-acquire

echo
echo "==> done. Station services:"
systemctl --no-pager --no-legend is-active ecallisto-web ecallisto-acquire || true
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "    Portal: http://${IP:-<station-ip>}:$PORT  (complete the setup wizard)"
echo "    If a serial Callisto was just plugged/added, reboot once so the"
echo "    dialout group + udev rules fully apply."
