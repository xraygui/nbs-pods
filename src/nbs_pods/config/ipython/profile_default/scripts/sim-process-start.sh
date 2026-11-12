#!/usr/bin/bash
# Run one extra nbs-sim process: the devices with _process = $NBS_SIM_PROCESS.
set -e
set -o xtrace
pip install git+https://github.com/cjtitus/caproto.git@no_macros
nbs-sim --startup-dir /usr/local/share/ipython/profile_default/startup --process "${NBS_SIM_PROCESS:?set NBS_SIM_PROCESS}" --list-pvs
