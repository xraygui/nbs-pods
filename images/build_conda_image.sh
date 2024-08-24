#!/usr/bin/env bash
set -e
set -o xtrace

version="0.0.1"
# Define the container
container=$(buildah from fedora)

# Define the environment variable
buildah config --env CONDA_DIR=/opt/conda $container

# Install Miniconda
buildah run $container -- dnf install -y wget git g++ gcc
buildah run $container -- bash -c "wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && /bin/bash ~/miniconda.sh -b -p /opt/conda"

# Update the PATH environment variable
buildah config --env PATH=/opt/conda/bin:$PATH $container

# Commit the container
buildah commit $container conda-base:$version
buildah commit $container conda-base:latest

# Clean up
buildah rm $container

