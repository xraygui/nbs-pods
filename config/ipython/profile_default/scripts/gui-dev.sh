#!/usr/bin/bash
set -e
set -o xtrace
pip install -e /usr/local/src/xraygui/nbs-gui
$(dirname "$0")/gui-start.sh

