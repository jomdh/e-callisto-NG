#!/usr/bin/env bash
# Dev runner: run the tests, then (re)start the e-Callisto NG web app so you can
# click through the changes. Uses a throwaway DB + data dir under .temp/.
#
#   scripts/dev-run.sh            # run tests, then restart the server
#   scripts/dev-run.sh --no-tests # skip tests, just restart
#   scripts/dev-run.sh --fresh    # wipe the DB first (re-runs the setup wizard)
#
# Stop it with Ctrl-C. The server auto-reloads when you edit src/.
set -euo pipefail
cd "$(dirname "$0")/.."

VENV=.venv
RUNTIME="$PWD/.temp"
DB="$RUNTIME/ecallisto.db"
DATA="$RUNTIME/data"
PORT="${ECALLISTO_PORT:-8000}"

RUN_TESTS=1
FRESH=0
for arg in "$@"; do
    case "$arg" in
        --no-tests) RUN_TESTS=0 ;;
        --fresh) FRESH=1 ;;
        *) echo "unknown flag: $arg" ; exit 2 ;;
    esac
done

# --- virtualenv -----------------------------------------------------------
if [ ! -x "$VENV/bin/python" ]; then
    echo "== creating venv + installing deps =="
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -e ".[dev]"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

export PYTHONPATH="$PWD/src"

# --- tests ----------------------------------------------------------------
if [ "$RUN_TESTS" = 1 ]; then
    echo "== running tests =="
    pytest -q -p no:warnings
    echo "== tests passed =="
fi

# --- stop any running server ---------------------------------------------
echo "== stopping any server on :$PORT =="
lsof -ti "tcp:$PORT" | xargs kill 2>/dev/null || true
sleep 0.5

# --- runtime env ----------------------------------------------------------
mkdir -p "$DATA"
if [ "$FRESH" = 1 ]; then
    rm -f "$DB"
    echo "== fresh DB: the setup wizard will run again =="
fi

export ECALLISTO_DB_URL="sqlite:///$DB"
export ECALLISTO_DATA_DIR="$DATA"
export ECALLISTO_BIND=127.0.0.1
export ECALLISTO_PORT="$PORT"
# short tick intervals so you can watch the scheduler/uploader act
export ECALLISTO_SCHEDULER_TICK_SECONDS=15
export ECALLISTO_UPLOADER_TICK_SECONDS=20

echo
echo "== e-Callisto NG running =="
echo "   Portal:    http://127.0.0.1:$PORT"
echo "   API docs:  http://127.0.0.1:$PORT/docs"
echo "   (Ctrl-C to stop; edits under src/ auto-reload)"
echo
exec uvicorn ecallisto_ng.api.app:create_app --factory \
    --host 127.0.0.1 --port "$PORT" --reload --reload-dir src
