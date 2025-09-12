#!/usr/bin/bash
set -e
set -o xtrace
pip install -e /usr/local/src/xraygui/nbs-sim
$(dirname "$0")/sim-start.sh