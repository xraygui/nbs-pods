# NBS Pods

Containerized NBS (NIST Beamline Software) services for beamline simulation.

## Container Images

This repository provides containerized NBS services that can be run in two modes:

### Demo Mode (Pre-built Images)
Uses pre-built images from GitHub Container Registry (GHCR):
```bash
# Images are automatically built and pushed to:
# ghcr.io/xraygui/nbs-pods/bluesky:latest
# ghcr.io/xraygui/nbs-pods/nbs:latest  
# ghcr.io/xraygui/nbs-pods/nbs-gui:latest
```

### Development Mode (Local Builds)
Build images locally for development:
```bash
# Build all images
podman-compose -f docker-compose.build.yml build

# Build specific image
podman-compose -f docker-compose.build.yml build nbs

# Rebuild with no caching
podman-compose -f docker-compose.build.yml build --no-cache nbs_gui
```

## Image Dependencies

```
fedora → bluesky → nbs → nbs-gui
```

## Usage

### Demo Mode (Default)
```bash
# Start all services with pre-built images
./scripts/deploy.sh start

# Start specific services
./scripts/deploy.sh start gui queueserver

# Start demo services (bluesky-services, gui, queueserver, sim, viewer)
./scripts/deploy.sh demo
```

### Development Mode
```bash
# Build images locally first
podman-compose -f docker-compose.build.yml build

# Start specific services in development mode
./scripts/deploy.sh start --dev gui

# Mix normal and development mode
./scripts/deploy.sh start queueserver --dev gui
```

### Stopping Services
```bash
# Stop all services
./scripts/deploy.sh stop

# Stop specific services
./scripts/deploy.sh stop gui queueserver
```

## Available Services

- **bluesky-services**: Core infrastructure (Redis, MongoDB, Kafka, ZMQ proxies)
- **queueserver**: RE Manager for experiment orchestration
- **gui**: NBS GUI with display protocol detection (Wayland/X11)
- **sim**: NBS simulation services
- **viewer**: Additional viewing services (if configured)

## Development Workflow

### Docker Compose Override System

The deployment system uses Docker Compose's override mechanism to enable flexible configuration:

1. **Base Configuration**: Each service has a main `docker-compose.yml` file with default settings
2. **Override Files**: `docker-compose.override.yml` files (if present) are automatically composed with the main file
3. **Development Files**: `docker-compose.development.yml` files are applied when using the `--dev` flag

### Override Files (`docker-compose.override.yml`)

Override files allow local customization without modifying the base configuration:
- **Testing**: Override environment variables, ports, or volumes for testing
- **Bug Fixes**: Temporarily modify service parameters to work around issues
- **GUI Configuration**: Especially useful for display protocol issues (Wayland/X11)
- **Local Paths**: Mount local directories for configuration or data

Example override file:
```yaml
services:
  qs-gui:
    volumes:
      - ${HOME}/local-config:/etc/bluesky
    environment:
      - DEBUG=true
```

### Development Files (`docker-compose.development.yml`)

Development files are applied when using the `--dev` flag and typically:
- **Switch to Local Images**: Use locally built images instead of GHCR images
- **Config Mounts**: Mount configuration directories to test config changes
- **Code Mounts**: Mount local source code directories for live development
- **Local Installs**: Install packages from local paths with `pip install -e`
- **Debug Settings**: Enable debugging, logging, or development-specific configurations

Example development file which only mounts local config directories
```yaml
services:
  qs-gui:
    volumes:
      - ${NBS_PODS_DIR}/config/bluesky:/etc/bluesky
      - ${BEAMLINE_PODS_DIR}/config/ipython:/usr/local/share/ipython
      - ${NBS_PODS_DIR}/config/tiled:/etc/tiled
```

Example development file which installs local code
```yaml
services:
  nbs-sim:
    volumes:
      - ${NBSDIR}:/usr/local/src/xraygui
      - ${BEAMLINE_PODS_DIR}/config/ipython:/usr/local/share/ipython
    command: >
      bash -c "
        pip3 install --no-deps --no-build-isolation -e /usr/local/src/xraygui/nbs-sim/src &&
        nbs-sim --startup-dir /usr/local/share/ipython/profile_default/startup --list-pvs
      "
```
### File Resolution Order

The system resolves compose files in this order:
1. Base service file (e.g., `docker-compose.yml`)
2. Override file (`docker-compose.override.yml`) - if present
3. Development file (`docker-compose.development.yml`) - if `--dev` flag used

Later files override earlier ones, allowing for flexible configuration management.

## Configuration

Images include default configurations in `/etc/bluesky` and `/etc/tiled/profiles` which can be overridden with volume mounts in development mode. 