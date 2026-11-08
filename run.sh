#!/usr/bin/env bash
# One command: make the venv if needed, install requirements, start LumaSync, open the UI.
#   ./run.sh                         # demo track through the speakers, DMX if the cable is plugged in
#   ./run.sh --source mic            # live mic / line-in  (./run.sh --list-devices to pick --device N)
#   ./run.sh --mute --no-dmx         # silent, preview only
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Creating .venv ..."
  python3 -m venv .venv
fi
if ! .venv/bin/python -c "import numpy, scipy, sounddevice, soundfile, serial, websockets" 2>/dev/null; then
  echo "Installing requirements ..."
  .venv/bin/pip install -q -r requirements.txt
fi
echo "Starting LumaSync on http://localhost:8765  (Ctrl+C to stop)"
exec .venv/bin/python -m lumasync.app --open "$@"
