#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export NBS_PODS_DIR="$(dirname "$SCRIPT_DIR")"
export BEAMLINE_PODS_DIR="$NBS_PODS_DIR"  # For demo, nbs-pods is its own beamline
export BEAMLINE_NAME="demo"

# Source the library functions
source "$NBS_PODS_DIR/scripts/nbs-pods-lib.sh"

# Define demo beamline services
BEAMLINE_SERVICES=(
    "sim"  # Simulation service for demo
)

# Combine all services
ALL_SERVICES=(
    "${BASE_SERVICES[@]}"
    "${BEAMLINE_SERVICES[@]}"
)

usage() {
    echo "Usage: $0 [start [--dev]|stop] [service1 service2 ...]"
    echo "If no services are specified, all will be managed."
    echo ""
    print_usage
    echo ""
    echo "Note: For image building, use ./scripts/build-images.sh"
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
else
    usage
fi 