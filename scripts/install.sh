#!/usr/bin/env bash
# Install e-Callisto NG on a Debian/Raspbian station (run as root).
set -euo pipefail

APP_DIR=/opt/ecallisto-ng
DATA_DIR=/var/lib/callisto
CONF_DIR=/etc/callisto
USER=callisto

echo ">> creating user and directories"
id -u "$USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" "$USER"
install -d -o "$USER" -g "$USER" "$APP_DIR" "$DATA_DIR" "$CONF_DIR"

echo ">> installing into a virtualenv (--system-site-packages so an apt"
echo "   SoapySDR for the RX-888 stays visible)"
python3 -m venv --system-site-packages "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install .

echo ">> writing default environment (edit as needed)"
if [ ! -f "$CONF_DIR/ecallisto.env" ]; then
    cat > "$CONF_DIR/ecallisto.env" <<EOF
ECALLISTO_BIND=0.0.0.0
ECALLISTO_PORT=8000
ECALLISTO_DATA_DIR=$DATA_DIR
ECALLISTO_CONFIG_DIR=$CONF_DIR
EOF
fi
chown "$USER:$USER" "$CONF_DIR/ecallisto.env"

echo ">> installing systemd unit"
install -m 0644 packaging/systemd/ecallisto-web.service \
    /etc/systemd/system/ecallisto-web.service
systemctl daemon-reload
systemctl enable --now ecallisto-web

echo ">> done. Open the portal and complete the setup wizard."
