#!/usr/bin/env bash
# Run e-Callisto NG on this station, reachable over the LAN/VPN.
# Pull-and-run: the first run creates a venv + .env, later runs just start it.
#
#   ./scripts/run.sh
#
# The venv is created with --system-site-packages so an apt/conda-installed
# SoapySDR (the RX-888 backend, driver=rx888) stays visible. If SoapySDR lives
# only in a conda env, activate that env first and `pip install -e .` there.
set -euo pipefail
cd "$(dirname "$0")/.."

VENV=.venv
PY=${PYTHON:-python3}

if [ ! -x "$VENV/bin/python" ]; then
  echo "== creating venv (--system-site-packages, for SoapySDR/RX-888) =="
  "$PY" -m venv --system-site-packages "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -e .
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"

# Self-heal deps after a `git pull` adds one (e.g. the websocket library the
# live waterfall needs) without recreating the venv.
if ! python -c "import websockets" >/dev/null 2>&1; then
  echo "== installing/updating dependencies =="
  pip install -q -e .
fi

# Preflight: serial access. Recording from a serial Callisto (/dev/ttyUSB*)
# needs the 'dialout' group; warn early instead of failing at record time.
if ! id -nG "$USER" 2>/dev/null | tr ' ' '\n' | grep -qx dialout; then
  if ls /dev/ttyUSB* /dev/ttyACM* >/dev/null 2>&1; then
    echo
    echo "WARNING: '$USER' is not in the 'dialout' group -- opening a serial"
    echo "  Callisto will be denied (Permission denied: /dev/ttyUSB0)."
    echo "  Fix once:  sudo usermod -aG dialout $USER"
    echo "  then log out and back in (or reboot), and re-run this script."
    echo
  fi
fi

if [ ! -f .env ]; then
  echo "== writing .env (generated secret key + repo-local ./data) =="
  cp .env.example .env
  KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  python - "$KEY" <<'PY'
import pathlib, sys
p = pathlib.Path(".env"); key = sys.argv[1]
out = []
for ln in p.read_text().splitlines():
    if ln.startswith("ECALLISTO_SECRET_KEY="):
        ln = f"ECALLISTO_SECRET_KEY={key}"
    if ln.startswith("ECALLISTO_DATA_DIR="):
        ln = "ECALLISTO_DATA_DIR=./data"
    out.append(ln)
p.write_text("\n".join(out) + "\n")
PY
fi

# shellcheck disable=SC1091
set -a; . ./.env; set +a
mkdir -p "${ECALLISTO_DATA_DIR:-./data}"
BIND=${ECALLISTO_BIND:-0.0.0.0}
PORT=${ECALLISTO_PORT:-8000}
IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo
echo "== e-Callisto NG  ->  http://${IP:-<this-host>}:$PORT   (bind $BIND) =="
echo "   First run opens the setup wizard (no default credentials)."
echo "   RX-888 check: python3 scripts/scan_devices.py"
echo
exec uvicorn ecallisto_ng.api.app:create_app --factory \
    --host "$BIND" --port "$PORT"
