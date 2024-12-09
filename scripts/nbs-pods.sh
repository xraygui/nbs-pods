#!/bin/bash

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Allow overriding the beamline repo location
BEAMLINE_PODS_DIR=${BEAMLINE_PODS_DIR:-"$(dirname "$BASE_DIR")/${BEAMLINE_NAME}-pods"}

# Core services that are always available
CORE_SERVICES=(
    "core"              # Renamed from bluesky-services
    "queueserver"
    "gui"
)

# Template services that can be instantiated
TEMPLATE_SERVICES=(
    "bsui"
)

# Load beamline-specific services if available
if [ -f "$BEAMLINE_PODS_DIR/scripts/services.sh" ]; then
    source "$BEAMLINE_PODS_DIR/scripts/services.sh"
else
    BEAMLINE_SERVICES=()
fi

# Combine all services
ALL_SERVICES=(
    "${CORE_SERVICES[@]}"
    "${TEMPLATE_SERVICES[@]}"
    "${BEAMLINE_SERVICES[@]}"
)

# Function to get the compose file path for a service
get_compose_file() {
    local service=$1
    local compose_file=""
    
    # Check if service has beamline override
    if [ -f "$BEAMLINE_PODS_DIR/compose/override/$service/docker-compose.yml" ]; then
        compose_file="$BEAMLINE_PODS_DIR/compose/override/$service/docker-compose.yml"
    # Check if service is a template
    elif [ -d "$BASE_DIR/compose/templates/$service" ]; then
        compose_file="$BASE_DIR/compose/templates/$service/docker-compose.yml"
    # Check if service is a core service
    elif [ -f "$BASE_DIR/compose/core/$service/docker-compose.yml" ]; then
        compose_file="$BASE_DIR/compose/core/$service/docker-compose.yml"
    # Check if service is beamline-specific
    elif [ -f "$BEAMLINE_PODS_DIR/compose/beamline/$service/docker-compose.yml" ]; then
        compose_file="$BEAMLINE_PODS_DIR/compose/beamline/$service/docker-compose.yml"
    fi
    
    echo "$compose_file"
}

start_service() {
    local service=$1
    local dev_mode=$2
    echo "Starting $service..."
    
    local compose_file=$(get_compose_file "$service")
    if [ -z "$compose_file" ]; then
        echo "Error: No compose file found for service $service"
        return 1
    fi
    
    # Set up compose override chain
    local compose_files=("$compose_file")
    
    # Add dev override if in dev mode
    if [ "$dev_mode" = true ] && [ -f "${compose_file%/*}/docker-compose.override.yml" ]; then
        compose_files+=("${compose_file%/*}/docker-compose.override.yml")
    fi
    
    # Add beamline override if it exists
    if [ -f "$BEAMLINE_PODS_DIR/compose/override/$service/docker-compose.override.yml" ]; then
        compose_files+=("$BEAMLINE_PODS_DIR/compose/override/$service/docker-compose.override.yml")
    fi
    
    # Build the COMPOSE_FILE string
    local compose_string=""
    for file in "${compose_files[@]}"; do
        if [ -n "$compose_string" ]; then
            compose_string="$compose_string:"
        fi
        compose_string="$compose_string$file"
    done
    
    COMPOSE_FILE="$compose_string" podman-compose up -d
}

stop_service() {
    local service=$1
    echo "Stopping $service..."
    
    local compose_file=$(get_compose_file "$service")
    if [ -z "$compose_file" ]; then
        echo "Error: No compose file found for service $service"
        return 1
    fi
    
    COMPOSE_FILE="$compose_file" podman-compose down -v
}

build_image() {
    local image=$1
    echo "Building $image..."
    bash "$BASE_DIR/images/$image/build_${image}_image.sh"
}

start_all_services() {
    local dev_mode=$1
    for service in "${ALL_SERVICES[@]}"; do
        start_service "$service" "$dev_mode"
    done
}

stop_all_services() {
    for ((i=${#ALL_SERVICES[@]}-1; i>=0; i--)); do
        stop_service "${ALL_SERVICES[i]}"
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
    echo "Core services:"
    for service in "${CORE_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo "Template services:"
    for service in "${TEMPLATE_SERVICES[@]}"; do
        echo "  - $service"
    done
    if [ ${#BEAMLINE_SERVICES[@]} -gt 0 ]; then
        echo "Beamline services:"
        for service in "${BEAMLINE_SERVICES[@]}"; do
            echo "  - $service"
        done
    fi
    echo ""
    echo "Available images:"
    for image in "${IMAGES[@]}"; do
        echo "  - $image"
    done
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