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

# Function to get the override file path for a service
get_compose_override() {
    local service=$1
    local override_file=""
    
    # Check for beamline override first
    if [ -f "$BEAMLINE_PODS_DIR/compose/$service/docker-compose.override.yml" ]; then
        override_file="$BEAMLINE_PODS_DIR/compose/$service/docker-compose.override.yml"
    # Then check for base override
    elif [ -f "$NBS_PODS_DIR/compose/$service/docker-compose.override.yml" ]; then
        override_file="$NBS_PODS_DIR/compose/$service/docker-compose.override.yml"
    fi
    echo "$override_file"
}

# Function to get the development file path for a service
get_compose_development() {
    local service=$1
    local dev_file=""
    
    # Check for beamline development file first
    if [ -f "$BEAMLINE_PODS_DIR/compose/$service/docker-compose.development.yml" ]; then
        dev_file="$BEAMLINE_PODS_DIR/compose/$service/docker-compose.development.yml"
    # Then check for base development file
    elif [ -f "$NBS_PODS_DIR/compose/$service/docker-compose.development.yml" ]; then
        dev_file="$NBS_PODS_DIR/compose/$service/docker-compose.development.yml"
    fi
    echo "$dev_file"
}

start_service() {
    local service=$1
    local dev_mode=$2
    echo "Starting $service$([ "$dev_mode" = true ] && echo " (dev mode)")..."
    
    local compose_file=$(get_compose_file "$service")
    if [ -z "$compose_file" ]; then
        echo "Error: No compose file found for service $service"
        echo "Searched for: $compose_file"
        return 1
    fi
    
    # Set up compose file chain
    local compose_files=("$compose_file")
    echo "  Using compose files:"
    echo "    - $compose_file (base)"
    
    # Always add override if it exists
    local override_file=$(get_compose_override "$service")
    if [ -n "$override_file" ]; then
        compose_files+=("$override_file")
        echo "    - $override_file (override)"
    fi
    
    # Add development file if in dev mode
    if [ "$dev_mode" = true ]; then
        local dev_file=$(get_compose_development "$service")
        if [ -n "$dev_file" ]; then
            compose_files+=("$dev_file")
            echo "    - $dev_file (development)"
        fi
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
    
    # Include override file if it exists
    local override_file=$(get_compose_override "$service")
    local compose_string="$compose_file"
    if [ -n "$override_file" ]; then
        compose_string="$compose_string:$override_file"
    fi
    
    COMPOSE_FILE="$compose_string" podman-compose down -v
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