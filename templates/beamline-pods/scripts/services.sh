#!/bin/bash

# The services.sh file declares which services are specific to your beamline.
# This file is sourced by deploy.sh and defines the BEAMLINE_SERVICES array.
# Each service listed here should have a corresponding directory in compose/beamline/.

# Define beamline-specific services
BEAMLINE_SERVICES=(
    # Add your beamline-specific services here
    # Example: "custom-detector"    # Uses compose/beamline/custom-detector/
) 