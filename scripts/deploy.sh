#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export NBS_PODS_DIR="$(dirname "$SCRIPT_DIR")"
export BEAMLINE_PODS_DIR="$NBS_PODS_DIR"
export BEAMLINE_NAME="demo"
export HOST_UID=$(id -u)

if command -v nbs-pods &> /dev/null; then
    exec nbs-pods "$@"
elif command -v pixi &> /dev/null && [ -f "$NBS_PODS_DIR/pyproject.toml" ]; then
    cd "$NBS_PODS_DIR"
    exec pixi run nbs-pods "$@"
else
    echo "Error: nbs-pods CLI not found. Install nbs-pods or use pixi." >&2
    exit 1
fi 