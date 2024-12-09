#!/bin/bash

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <beamline-name>"
    echo "Example: $0 nexafs"
    exit 1
fi

BEAMLINE_NAME="$1"
REPO_NAME="${BEAMLINE_NAME}-pods"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

if [ -d "$REPO_NAME" ]; then
    echo "Error: Directory $REPO_NAME already exists"
    exit 1
fi

echo "Creating $REPO_NAME repository..."

# Create the basic directory structure
mkdir -p "$REPO_NAME"/{compose/,config/ipython/profile_default/startup,scripts,examples}

# Create a basic deploy.sh script
cat > "$REPO_NAME/scripts/deploy.sh" << 'EOF'
#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BEAMLINE_PODS_DIR="$(dirname "$SCRIPT_DIR")"
export NBS_PODS_DIR="$(dirname "$BEAMLINE_PODS_DIR")/nbs-pods"
export BEAMLINE_NAME="$(basename "$BEAMLINE_PODS_DIR" | sed 's/-pods$//')"

if [ ! -d "$NBS_PODS_DIR" ]; then
    echo "Error: nbs-pods directory not found at $NBS_PODS_DIR"
    echo "Please ensure nbs-pods is cloned in the same parent directory as this repository"
    exit 1
fi

# Source the library functions
source "$NBS_PODS_DIR/scripts/nbs-pods-lib.sh"

# Load beamline-specific services
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

usage() {
    echo "Usage: $0 [start [--dev]|stop|build] [service1 service2 ... | image1 image2 ...]"
    echo "If no services or images are specified, all will be managed."
    echo ""
    print_usage
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

echo "$BEAMLINE_NAME-pods operation completed successfully."
EOF

# Make deploy.sh executable
chmod +x "$REPO_NAME/scripts/deploy.sh"

# Create a basic docker-compose override template
cat > "$REPO_NAME/examples/docker-compose.override.yml" << 'EOF'
# Override file for customizing core services
version: '3'

services:
  # Example override for bsui service
  acq_bsui:
    volumes:
      # Add beamline-specific volumes here
      - ../../config/ipython:/usr/local/share/ipython
    environment:
      # Add beamline-specific environment variables here
      - BEAMLINE_CONFIG=/path/to/config

  # Example override for queue server
  acq_qs:
    volumes:
      # Add beamline-specific volumes here
      - ../../config/ipython:/usr/local/share/ipython
EOF

# Create a basic beamline.toml template
cat > "$REPO_NAME/config/ipython/profile_default/startup/beamline.toml" << 'EOF'
[configuration]
baseline = []
has_slits = false
has_motorized_samples = false
has_motorized_eref = false
has_polarization = false

[detector_sets.default]
primary = ""
normalization = ""
reference = ""

[devices]

[settings]
modules = []

[settings.plans]

[settings.redis.md]
host = "redis"
prefix = ""

[settings.redis.info]
host = "redisInfo"
prefix = ""
port = 60737
db = 4
EOF

# Create a basic devices.toml template
cat > "$REPO_NAME/config/ipython/profile_default/startup/devices.toml" << 'EOF'
# Define your beamline-specific devices here
[motors]

[detectors]

[shutters]
EOF

# Create a basic README
cat > "$REPO_NAME/README.md" << EOF
# $REPO_NAME

This repository contains the beamline-specific configuration and services for the $BEAMLINE_NAME beamline.
It is designed to work with the nbs-pods framework.

## Prerequisites

- nbs-pods repository cloned in the same parent directory as this repository
- Docker and docker-compose installed

## Directory Structure

- \`compose/\`: Contains beamline-specific services and overrides
- \`config/\`: Contains beamline-specific configuration
- \`scripts/\`: Contains deployment and utility scripts

## Usage

To start all services:
\`\`\`bash
./scripts/deploy.sh start
\`\`\`

To start specific services:
\`\`\`bash
./scripts/deploy.sh start service1 service2
\`\`\`

To stop all services:
\`\`\`bash
./scripts/deploy.sh stop
\`\`\`

## Configuration

1. Edit \`config/ipython/profile_default/startup/beamline.toml\` to configure beamline settings
2. Edit \`config/ipython/profile_default/startup/devices.toml\` to configure devices
3. Add beamline-specific services in \`compose/<service>/\`
4. Customize core service settings in \`compose/<service>/docker-compose.override.yml\`
EOF

echo "Created $REPO_NAME repository with the following structure:"
if command -v tree >/dev/null 2>&1; then
    tree "$REPO_NAME"
else
    ls -R "$REPO_NAME"
fi

echo -e "\nNext steps:"
echo "1. Edit $REPO_NAME/config/ipython/profile_default/startup/beamline.toml"
echo "2. Edit $REPO_NAME/config/ipython/profile_default/startup/devices.toml"
echo "3. Add your beamline-specific services in $REPO_NAME/compose/"
echo "4. Customize core services in $REPO_NAME/compose/<service>/docker-compose.override.yml"
