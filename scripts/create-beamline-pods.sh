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
PARENT_DIR="$(dirname "$BASE_DIR")"
TARGET_DIR="$PARENT_DIR/$REPO_NAME"

echo -e "\nWill create $REPO_NAME in:"
echo "$TARGET_DIR"
read -p "Is this correct? [Y/n] " response

if [[ "$response" =~ ^[Nn] ]]; then
    echo "Aborting."
    exit 1
fi

if [ -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR already exists"
    exit 1
fi

echo "Creating $REPO_NAME repository..."

# Create the basic directory structure
mkdir -p "$TARGET_DIR"/{compose/,config/ipython/profile_default/startup,scripts,examples,images}

# Create a basic deploy.sh script
cat > "$TARGET_DIR/scripts/deploy.sh" << 'EOF'
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
    "${BASE_SERVICES[@]}"
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
chmod +x "$TARGET_DIR/scripts/deploy.sh"

# Create a basic docker-compose override template
cat > "$TARGET_DIR/examples/docker-compose.override.yml" << 'EOF'
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
cat > "$TARGET_DIR/config/ipython/profile_default/startup/beamline.toml" << 'EOF'
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
cat > "$TARGET_DIR/config/ipython/profile_default/startup/devices.toml" << 'EOF'
# Define your beamline-specific devices here
[motors]

[detectors]

[shutters]
EOF

# Create a basic README
cat > "$TARGET_DIR/README.md" << EOF
# $REPO_NAME

This repository contains the beamline-specific configuration and services for the $BEAMLINE_NAME beamline.
It is designed to work with the nbs-pods framework.

## Prerequisites

- nbs-pods repository cloned in the same parent directory as this repository
- Docker and docker-compose installed

## Directory Structure

- \`compose/\`: Contains beamline-specific services and overrides
  - \`<service>/\`: Each service has its own directory with docker-compose files
    - \`docker-compose.yml\`: Main service definition
    - \`docker-compose.override.yml\`: Optional overrides (always applied)
    - \`docker-compose.development.yml\`: Development settings (applied with --dev)
- \`config/\`: Contains beamline-specific configuration
- \`scripts/\`: Contains deployment and utility scripts
  - \`deploy.sh\`: Main deployment script
  - \`services.sh\`: Defines beamline-specific services

## Service Management

The \`services.sh\` file is used to declare which services are specific to your beamline. 
This file is sourced by \`deploy.sh\` and should define a \`BEAMLINE_SERVICES\` array.
Each service listed in this array should have a corresponding directory in \`compose/<service>/\`.

For example, if your beamline has a custom detector service:
\`\`\`bash
# scripts/services.sh
BEAMLINE_SERVICES=(
    "custom-detector"    # Uses compose/custom-detector/
)
\`\`\`

### Service Configuration Files

Each service can have up to three configuration files:

1. \`docker-compose.yml\`: Base configuration
   - Required for all services
   - Contains the core service definition

2. \`docker-compose.override.yml\`: Standard overrides
   - Optional
   - Always applied if present
   - Use for permanent customizations

3. \`docker-compose.development.yml\`: Development settings
   - Optional
   - Only applied when using \`--dev\` flag
   - Use for development-specific settings (volumes, ports, etc.)

For example, to override a base service from nbs-pods:

\`\`\`
compose/
└── bsui/
    ├── docker-compose.yml          # Base configuration
    ├── docker-compose.override.yml # Always applied
    └── docker-compose.development.yml # Applied with --dev flag
\`\`\`

## Usage

To start all services:
\`\`\`bash
./scripts/deploy.sh start           # Normal mode
./scripts/deploy.sh start --dev     # Development mode
\`\`\`

To start specific services:
\`\`\`bash
./scripts/deploy.sh start service1 service2
./scripts/deploy.sh start --dev service1 service2
\`\`\`

To stop all services:
\`\`\`bash
./scripts/deploy.sh stop
\`\`\`

## Configuration

1. Edit \`config/ipython/profile_default/startup/beamline.toml\` to configure beamline settings
2. Edit \`config/ipython/profile_default/startup/devices.toml\` to configure devices
3. Add beamline-specific services in \`compose/<service>/\`
4. Define beamline services in \`scripts/services.sh\`
EOF

echo "Created $REPO_NAME repository with the following structure:"
if command -v tree >/dev/null 2>&1; then
    tree "$TARGET_DIR"
else
    ls -R "$TARGET_DIR"
fi

echo "Initializing git repository..."
cd "$TARGET_DIR"

# Initialize git repository
git init

# Add initial files
git add scripts/deploy.sh \
    config/ipython/profile_default/startup/beamline.toml \
    config/ipython/profile_default/startup/devices.toml \
    README.md

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/

# Environment
.env
.venv/
env/
venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# QueueServer
config/ipython/profile_default/history.sqlite
config/ipython/profile_default/startup/existing_plans_and_devices.yaml
EOF

# Add .gitignore
git add .gitignore

# Initial commit
git commit -m "Initial commit for $REPO_NAME

Created with create-beamline-pods.sh script.
Includes:
- Basic directory structure
- Deploy script
- Configuration templates
- README"

echo -e "\nGit repository initialized with initial commit."
echo "Next steps:"
echo "1. Edit $REPO_NAME/config/ipython/profile_default/startup/beamline.toml"
echo "2. Edit $REPO_NAME/config/ipython/profile_default/startup/devices.toml"
echo "3. Add your beamline-specific services in $REPO_NAME/compose/"
echo "4. Customize core services in $REPO_NAME/compose/<service>/docker-compose.override.yml"
echo "5. Push to a remote repository if desired"

# Create a basic services.sh template
cat > "$REPO_NAME/scripts/services.sh" << 'EOF'
#!/bin/bash

# The services.sh file declares which services are specific to your beamline.
# This file is sourced by deploy.sh and defines the BEAMLINE_SERVICES array.
# Each service listed here should have a corresponding directory in compose/<service>/.

# Define beamline-specific services
BEAMLINE_SERVICES=(
    # Add your beamline-specific services here
    # Example: "custom-detector"    # Uses compose/custom-detector/
)
EOF

chmod +x "$REPO_NAME/scripts/services.sh"
