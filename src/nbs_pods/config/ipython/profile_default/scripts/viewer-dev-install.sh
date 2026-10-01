#!/usr/bin/bash
set -e
set -o xtrace
PACKAGE_DIR=/usr/local/src/collection_packages
pip install -e $PACKAGE_DIR/nbs-viewer
