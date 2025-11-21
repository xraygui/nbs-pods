#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BEAMLINE_PODS_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$SCRIPT_DIR/deploy.py" ]; then
    exec python3 "$SCRIPT_DIR/deploy.py" "$@"
elif command -v nbs-pods &> /dev/null; then
    BEAMLINE_NAME="$(basename "$BEAMLINE_PODS_DIR" | sed 's/-pods$//')"
    export BEAMLINE_PODS_DIR
    export BEAMLINE_NAME
    export HOST_UID=$(id -u)
    exec nbs-pods "$@"
elif command -v pixi &> /dev/null && [ -f "$BEAMLINE_PODS_DIR/pixi.toml" ]; then
    cd "$BEAMLINE_PODS_DIR"
    exec pixi run python scripts/deploy.py "$@"
else
    echo "Error: nbs-pods CLI not found. Install dependencies with: pixi install" >&2
    exit 1
fi 