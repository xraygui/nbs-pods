#!/usr/bin/bash
set -e
set -o xtrace
PACKAGE_DIR=/usr/local/src/collection_packages
pip install git+https://github.com/cjtitus/caproto.git@no_macros
pip install -e $PACKAGE_DIR/nbs-sim
