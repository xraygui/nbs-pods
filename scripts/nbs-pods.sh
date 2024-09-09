#!/bin/bash

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Define the list of services
SERVICES=(
    "bluesky-services"
    "queueserver"
    "sim"
    "tes"
    "gui"
)

IMAGES=(
    "conda"
    "bluesky"
    "nbs"
)

start_service() {
    local service=$1
    local dev_mode=$2
    echo "Starting $service..."
    if [ "$dev_mode" = true ]; then
        (cd "$BASE_DIR/compose/$service" && podman-compose up -d)
    else
        podman-compose -f "$BASE_DIR/compose/$service/docker-compose.yml" up -d
    fi
}

stop_service() {
    local service=$1
    echo "Stopping $service..."
    podman-compose -f "$BASE_DIR/compose/$service/docker-compose.yml" down
}

build_image() {
    local image=$1
    echo "Building $image..."
    bash "$BASE_DIR/images/$image/build_${image}_image.sh"
}

start_all_services() {
    local dev_mode=$1
    for service in "${SERVICES[@]}"; do
        start_service "$service" "$dev_mode"
    done
}

stop_all_services() {
    for ((i=${#SERVICES[@]}-1; i>=0; i--)); do
        stop_service "${SERVICES[i]}"
    done
}

build_all_images() {
    for image in "${IMAGES[@]}"; do
        build_image "$image"
    done
}

usage() {
    echo "Usage: $0 [start [--dev]|stop|build] [service1 service2 ... | image1 image2 ...]"
    echo "If no services or images are specified, all will be managed."
    echo ""
    echo "Available services:"
    for service in "${SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo "Available images:"
    for image in "${IMAGES[@]}"; do
        echo "  - $image"
    done
    echo ""
    echo "Examples:"
    echo "  $0 start                  # Start all services"
    echo "  $0 start --dev            # Start all services in dev mode"
    echo "  $0 start queueserver gui  # Start specific services"
    echo "  $0 stop queueserver gui   # Stop specific services"
    echo "  $0 build                  # Build all images"
    echo "  $0 build conda nbs        # Build specific images"
    exit 1
}

# Main execution
if [ $# -eq 0 ]; then
    usage
elif [ "$1" = "start" ]; then
    shift
    dev_mode=false
    if [ "$1" = "--dev" ]; then
        dev_mode=true
        shift
    fi
    if [ $# -eq 0 ]; then
        start_all_services "$dev_mode"
    else
        for service in "$@"; do
            start_service "$service" "$dev_mode"
        done
    fi
elif [ "$1" = "stop" ]; then
    shift
    if [ $# -eq 0 ]; then
        stop_all_services
    else
        for service in "$@"; do
            stop_service "$service"
        done
    fi
elif [ "$1" = "build" ]; then
    shift
    if [ $# -eq 0 ]; then
        build_all_images
    else
        for image in "$@"; do
            build_image "$image"
        done
    fi
else
    usage
fi

echo "NBS pods operation completed successfully."