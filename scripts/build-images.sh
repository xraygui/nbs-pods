#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NBS_PODS_DIR="$(dirname "$SCRIPT_DIR")"

# Define available images
IMAGES=(
    "conda"
    "bluesky"
    "nbs"
)

build_image() {
    local image=$1
    echo "Building $image..."
    bash "$NBS_PODS_DIR/images/$image/build_${image}_image.sh"
}

build_all_images() {
    for image in "${IMAGES[@]}"; do
        build_image "$image"
    done
}

usage() {
    echo "Usage: $0 [image1 image2 ...]"
    echo "If no images are specified, all will be built."
    echo ""
    echo "Available images:"
    for image in "${IMAGES[@]}"; do
        echo "  - $image"
    done
    exit 1
}

# Main execution
if [ $# -eq 0 ]; then
    build_all_images
else
    for image in "$@"; do
        if [[ ! " ${IMAGES[@]} " =~ " ${image} " ]]; then
            echo "Error: Unknown image '$image'"
            echo ""
            usage
        fi
        build_image "$image"
    done
fi 