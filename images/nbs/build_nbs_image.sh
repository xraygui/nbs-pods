#! /usr/bin/bash
set -e
set -o xtrace

version="0.0.1"

container=$(buildah from bluesky)
buildah run $container -- pip3 install git+https://github.com/xraygui/nbs-core@v0.0.2
buildah run $container -- pip3 install git+https://github.com/xraygui/nbs-bl@v0.1.1
buildah run $container -- pip3 install git+https://github.com/xraygui/nbs-sim
buildah run $container -- pip3 install git+https://github.com/xraygui/livetable@v0.1.0



buildah unmount $container

buildah commit $container nbs:latest
buildah commit $container nbs:$version

buildah rm $container
