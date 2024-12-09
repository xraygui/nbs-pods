#!/bin/bash

# This file is meant to be sourced, not executed directly
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    echo "This script should be sourced from another script, not run directly"
    exit 1
fi

# Ensure required variables are set
if [ -z "$BEAMLINE_NAME" ]; then
    echo "Error: BEAMLINE_NAME must be set before sourcing this script"
    return 1
fi

if [ -z "$NBS_PODS_DIR" ]; then
    echo "Error: NBS_PODS_DIR must be set before sourcing this script"
    return 1
fi

# Base services provided by nbs-pods
BASE_SERVICES=(
    "bluesky-services"
    "queueserver"
    "bsui"
    "gui"
    "sim"
)

# Function to get the compose file path for a service
get_compose_file() {
    local service=$1
    local compose_file=""
    
    # Check for beamline override first
    if [ -f "$BEAMLINE_PODS_DIR/compose/$service/docker-compose.yml" ]; then
        compose_file="$BEAMLINE_PODS_DIR/compose/$service/docker-compose.yml"
    # Then check for base service
    elif [ -f "$NBS_PODS_DIR/compose/$service/docker-compose.yml" ]; then
        compose_file="$NBS_PODS_DIR/compose/$service/docker-compose.yml"
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

print_usage() {
    echo "Available services:"
    echo "Base services (can be overridden):"
    for service in "${BASE_SERVICES[@]}"; do
        echo "  - $service"
    done
    if [ ${#BEAMLINE_SERVICES[@]} -gt 0 ]; then
        echo "Beamline services:"
        for service in "${BEAMLINE_SERVICES[@]}"; do
            echo "  - $service"
        done
    fi
} 