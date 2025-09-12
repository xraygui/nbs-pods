#!/usr/bin/bash
set -e
set -o xtrace
pip install -e /usr/local/src/xraygui/nbs-viewer
$(dirname "$0")/viewer-start.sh