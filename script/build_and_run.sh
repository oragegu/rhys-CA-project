#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"
APP_NAME="kDrive-Link-Manager"
BUNDLE_ID="ca.rhys.kdrive-link-manager"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv314/bin/python"
APP_BUNDLE="$ROOT_DIR/dist/$APP_NAME.app"
APP_BINARY="$APP_BUNDLE/Contents/MacOS/$APP_NAME"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing $PYTHON. Create the documented Python 3.14 environment first." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import PyInstaller, requests, tkinter' >/dev/null 2>&1; then
  echo "The .venv314 environment needs PyInstaller, requests, and Tkinter." >&2
  exit 1
fi

pkill -x "$APP_NAME" >/dev/null 2>&1 || true

"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier "$BUNDLE_ID" \
  --paths "$ROOT_DIR/src" \
  --distpath "$ROOT_DIR/dist" \
  --workpath "$ROOT_DIR/build/macos" \
  --specpath "$ROOT_DIR/build/macos" \
  "$ROOT_DIR/run_app.py"

open_app() {
  /usr/bin/open -n "$APP_BUNDLE"
}

case "$MODE" in
  run)
    open_app
    ;;
  --debug|debug)
    lldb -- "$APP_BINARY"
    ;;
  --logs|logs)
    open_app
    /usr/bin/log stream --info --style compact --predicate "process == \"$APP_NAME\""
    ;;
  --telemetry|telemetry)
    open_app
    /usr/bin/log stream --info --style compact --predicate "subsystem == \"$BUNDLE_ID\""
    ;;
  --verify|verify)
    open_app
    sleep 2
    pgrep -f "$APP_BINARY" >/dev/null
    echo "$APP_NAME is running from $APP_BUNDLE"
    ;;
  *)
    echo "usage: $0 [run|--debug|--logs|--telemetry|--verify]" >&2
    exit 2
    ;;
esac
