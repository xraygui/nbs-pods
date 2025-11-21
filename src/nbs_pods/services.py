"""Service discovery and management."""

from pathlib import Path

from nbs_pods.config import get_beamline_pods_dir, get_nbs_pods_dir


BASE_SERVICES = [
    "bluesky-services",
    "queueserver",
    "gui",
    "sim",
    "viewer",
]


def discover_base_services():
    """
    Discover base services from nbs-pods compose directory.

    Returns
    -------
    list[str]
        List of base service names
    """
    nbs_pods_dir = get_nbs_pods_dir()
    compose_dir = nbs_pods_dir / "compose"

    if not compose_dir.exists():
        return BASE_SERVICES

    services = []
    for item in compose_dir.iterdir():
        if item.is_dir():
            docker_compose_files = item.glob("docker-compose*.yml")
            for compose_file in docker_compose_files:
                if compose_file.exists():
                    services.append(item.name)
                    break

    return sorted(services) if services else BASE_SERVICES


def discover_beamline_services():
    """
    Discover beamline-specific services.

    Returns
    -------
    list[str]
        List of beamline service names
    """
    beamline_pods_dir = get_beamline_pods_dir()
    nbs_pods_dir = get_nbs_pods_dir()

    if beamline_pods_dir == nbs_pods_dir:
        return []

    base_services = set(discover_base_services())
    services = []

    compose_dir = beamline_pods_dir / "compose"
    if compose_dir.exists():
        for item in compose_dir.iterdir():
            if item.is_dir() and item.name not in base_services:
                compose_file = item / "docker-compose.yml"
                if compose_file.exists():
                    services.append(item.name)

    beamline_subdir = compose_dir / "beamline"
    if beamline_subdir.exists():
        for item in beamline_subdir.iterdir():
            if item.is_dir():
                compose_file = item / "docker-compose.yml"
                if compose_file.exists() and item.name not in services:
                    services.append(item.name)

    return sorted(services)


def get_all_services():
    """
    Get all available services (base + beamline).

    Returns
    -------
    tuple[list[str], list[str]]
        (base_services, beamline_services)
    """
    base_services = discover_base_services()
    beamline_services = discover_beamline_services()
    return base_services, beamline_services
