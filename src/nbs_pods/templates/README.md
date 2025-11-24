# ${BEAMLINE_NAME}-pods

This repository contains the beamline-specific configuration and services for the ${BEAMLINE_NAME} beamline.
It is designed to work with the nbs-pods framework.

## Prerequisites

- [Pixi](https://pixi.sh) installed
- nbs-pods repository cloned in the same parent directory as this repository

## Setup

1. Install dependencies:
```bash
pixi install
```

## Directory Structure

- `compose/`: Contains beamline-specific services and overrides
  - `beamline/`: Beamline-specific services (auto-discovered)
  - `override/`: Customizations of nbs-pods services
- `config/`: Contains beamline-specific configuration
- `scripts/`: Contains deployment and utility scripts
  - `deploy.py`: Main deployment script (calls nbs-pods CLI)

## Service Management

Services are automatically discovered by scanning the `compose/` directory.
Beamline-specific services should be placed in `compose/beamline/` or directly in `compose/`.

For example, if your beamline has a custom detector service, create:
```
compose/
└── beamline/
    └── custom-detector/
        └── docker-compose.yml
```

The service will be automatically discovered and available for deployment.

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
pixi run start                      # Normal mode
pixi run start --dev service1       # Development mode for service1
```

Or use the nbs-pods CLI directly:
```bash
pixi run nbs-pods start             # Start all services
pixi run nbs-pods start service1 service2
pixi run nbs-pods start service1 --dev service2  # service2 in dev mode
```

To stop all services:
```bash
pixi run stop
# or
pixi run nbs-pods stop
```

To list available services:
```bash
pixi run nbs-pods list
```

## Configuration

1. Edit `config/ipython/profile_default/startup/beamline.toml` to configure beamline settings
2. Edit `config/ipython/profile_default/startup/devices.toml` to configure devices
3. Add beamline-specific services in `compose/beamline/` (services are auto-discovered)
4. Customize core services by creating override files in `compose/override/` 