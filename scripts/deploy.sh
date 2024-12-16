#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export NBS_PODS_DIR="$(dirname "$SCRIPT_DIR")"
export BEAMLINE_PODS_DIR="$NBS_PODS_DIR"  # For demo, nbs-pods is its own beamline
export BEAMLINE_NAME="demo"

export HOST_UID=$(id -u)

# Source the library functions
source "$NBS_PODS_DIR/scripts/nbs-pods-lib.sh"

if [ -f "$BEAMLINE_PODS_DIR/scripts/services.sh" ]; then
    source "$BEAMLINE_PODS_DIR/scripts/services.sh"
else
    BEAMLINE_SERVICES=()
fi

# Combine all services
ALL_SERVICES=(
    "${BASE_SERVICES[@]}"
    "${BEAMLINE_SERVICES[@]}"
)

usage() {
    echo "Usage: $0 [start|stop] [service1 service2 ... [--dev service3 service4 ...]]"
    echo ""
    echo "Examples:"
    echo "  $0 start                                    # Start all services normally"
    echo "  $0 start service1 service2                  # Start specific services normally"
    echo "  $0 start service1 --dev service2            # Start service1 normally, service2 in dev mode"
    echo "  $0 start --dev service1                     # Start service1 in dev mode"
    echo "  $0 stop                                     # Stop all services"
    echo ""
    print_usage
    exit 1
}

start_services() {
    local dev_mode=false
    local services=()
    
    # Process arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dev)
                dev_mode=true
                shift
                ;;
            *)
                # Start service with current dev_mode setting
                if [ -z "$1" ]; then
                    break
                fi
                start_service "$1" "$dev_mode"
                shift
                ;;
        esac
    done
}

stop_services() {
    if [ $# -eq 0 ]; then
        # Stop all services in reverse order
        for ((i=${#ALL_SERVICES[@]}-1; i>=0; i--)); do
            stop_service "${ALL_SERVICES[i]}"
        done
    else
        # Stop specific services
        for service in "$@"; do
            stop_service "$service"
        done
    fi
}

# Main execution
if [ $# -eq 0 ]; then
    usage
elif [ "$1" = "start" ]; then
    shift
    if [ $# -eq 0 ]; then
        # Start all services normally
        for service in "${ALL_SERVICES[@]}"; do
            start_service "$service" false
        done
    else
        start_services "$@"
    fi
elif [ "$1" = "stop" ]; then
    shift
    stop_services "$@"
else
    usage
fi 