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
TEMPLATE_DIR="$BASE_DIR/templates/beamline-pods"

if [ -d "$REPO_NAME" ]; then
    echo "Error: Directory $REPO_NAME already exists"
    exit 1
fi

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Error: Template directory not found at $TEMPLATE_DIR"
    exit 1
fi

echo "Creating $REPO_NAME repository..."

# Create the basic directory structure
mkdir -p "$REPO_NAME"/{compose/{override,beamline},config/ipython/profile_default/startup,scripts}

# Copy template files
cp -r "$TEMPLATE_DIR"/* "$REPO_NAME/"

# Replace placeholders in template files
find "$REPO_NAME" -type f -exec sed -i "s/\${BEAMLINE_NAME}/$BEAMLINE_NAME/g" {} +

# Make scripts executable
chmod +x "$REPO_NAME/scripts/"*.sh

echo "Created $REPO_NAME repository with the following structure:"
tree "$REPO_NAME"

echo -e "\nNext steps:"
echo "1. Edit $REPO_NAME/config/ipython/profile_default/startup/beamline.toml"
echo "2. Edit $REPO_NAME/config/ipython/profile_default/startup/devices.toml"
echo "3. Add beamline-specific services in $REPO_NAME/compose/beamline/"
echo "4. Customize core services in $REPO_NAME/compose/override/"
