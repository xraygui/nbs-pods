#! /usr/bin/bash
set -e
set -o xtrace

version="0.0.1"
container=$(buildah from conda-base)
buildah run $container -- conda install -yc conda-forge pyepics
buildah run $container -- pip3 install --pre databroker[all]
buildah run $container -- pip3 install bluesky
buildah run $container -- pip3 install nslsii tiled[all]
buildah run $container -- pip3 install git+https://github.com/bluesky/bluesky-adaptive.git@main#egg=bluesky-adaptive
buildah run $container -- pip3 install git+https://github.com/bluesky/bluesky-queueserver.git@main#egg=bluesky-queueserver

buildah unmount $container

buildah commit $container bluesky:latest
buildah commit $container bluesky:$version

buildah rm $container
