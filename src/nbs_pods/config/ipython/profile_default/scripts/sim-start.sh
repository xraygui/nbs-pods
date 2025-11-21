#!/usr/bin/bash
set -e
set -o xtrace
pip install git+https://github.com/cjtitus/caproto.git@no_macros
nbs-sim --startup-dir /usr/local/share/ipython/profile_default/startup --list-pvs