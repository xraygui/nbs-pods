#!/usr/bin/bash
set -e
set -o xtrace
pip install -e /usr/local/src/xraygui/nbs-core
pip install -e /usr/local/src/xraygui/nbs-bl
$(dirname "$0")/qs-start.sh