# ${BEAMLINE_NAME}-pods

This repository contains the beamline-specific configuration and services for the ${BEAMLINE_NAME} beamline.
It is designed to work with the nbs-pods framework.

## Prerequisites

- nbs-pods repository cloned in the same parent directory as this repository
- Docker and docker-compose installed

## Directory Structure

- `compose/`: Contains beamline-specific services and overrides
  - `beamline/`: Beamline-specific services
  - `override/`: Customizations of nbs-pods services
- `config/`: Contains beamline-specific configuration
- `scripts/`: Contains deployment and utility scripts
  - `deploy.sh`: Main deployment script
  - `services.sh`: Defines beamline-specific services

## Service Management

The `services.sh` file declares which services are specific to your beamline. 
This file is sourced by `deploy.sh` and should define a `BEAMLINE_SERVICES` array.
Each service listed in this array should have a corresponding directory in `compose/beamline/`.

For example, if your beamline has a custom detector service:
```bash
# scripts/services.sh
BEAMLINE_SERVICES=(
    "custom-detector"    # Uses compose/beamline/custom-detector/
)
```

### Service Configuration Files

Each service can have up to three configuration files:

1. `docker-compose.yml`: Base configuration
   - Required for all services
   - Contains the core service definition

2. `docker-compose.override.yml`: Standard overrides
   - Optional
   - Always applied if present
   - Use for permanent customizations

3. `docker-compose.development.yml`: Development settings
   - Optional
   - Only applied when using `--dev` flag
   - Use for development-specific settings (volumes, ports, etc.)

For example, to override a base service from nbs-pods:

```
compose/
└── override/
    └── bsui/
        ├── docker-compose.yml          # Base configuration
        ├── docker-compose.override.yml # Always applied
        └── docker-compose.development.yml # Applied with --dev flag
```

## Usage

To start all services:
```bash
./scripts/deploy.sh start           # Normal mode
./scripts/deploy.sh start --dev     # Development mode
```

To start specific services:
```bash
./scripts/deploy.sh start service1 service2
./scripts/deploy.sh start service1 --dev service2  # service2 in dev mode
```

To stop all services:
```bash
./scripts/deploy.sh stop
```

## Configuration

1. Edit `config/ipython/profile_default/startup/beamline.toml` to configure beamline settings
2. Edit `config/ipython/profile_default/startup/devices.toml` to configure devices
3. Add beamline-specific services in `compose/beamline/`
4. Define beamline services in `scripts/services.sh` 