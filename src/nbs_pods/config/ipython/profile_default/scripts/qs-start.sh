#!/usr/bin/bash
set -e
set -o xtrace
start-re-manager --redis-addr redis:6379 --zmq-publish-console ON --use-ipython-kernel ON --ipython-kernel-ip auto --startup-profile default