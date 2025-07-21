#! /usr/bin/bash
set -e
set -o xtrace

version="0.0.1"

container=$(buildah from bluesky)
buildah run $container -- pip3 install git+https://github.com/xraygui/nbs-core
buildah run $container -- pip3 install git+https://github.com/xraygui/nbs-bl
buildah run $container -- pip3 install git+https://github.com/xraygui/nbs-sim
buildah run $container -- pip3 install git+https://github.com/xraygui/livetable



buildah unmount $container

buildah commit $container nbs:latest
buildah commit $container nbs:$version

buildah rm $container
