"""Docker compose file resolution and chaining."""

from pathlib import Path

from nbs_pods.config import get_beamline_pods_dir, get_nbs_pods_dir
from nbs_pods.display import detect_display_protocol


def get_compose_file(service, verbose=False):
    """
    Get the base compose file for a service.

    Parameters
    ----------
    service : str
        Service name

    Returns
    -------
    Path | None
        Path to compose file, or None if not found
    """
    beamline_pods_dir = get_beamline_pods_dir()
    nbs_pods_dir = get_nbs_pods_dir()

    compose_file = None

    if service in ("gui", "viewer"):
        display_protocol = detect_display_protocol()
        print(f"Detected display protocol: {display_protocol}", flush=True)

        beamline_file = (
            beamline_pods_dir
            / "compose"
            / service
            / f"docker-compose.{display_protocol}.yml"
        )
        if verbose:
            print(f"Checking beamline file: {beamline_file}", flush=True)
        if beamline_file.exists():
            compose_file = beamline_file
        else:
            if verbose:
                print(f"Beamline file not found, checking nbs file", flush=True)
            nbs_file = (
                nbs_pods_dir
                / "compose"
                / service
                / f"docker-compose.{display_protocol}.yml"
            )
            if nbs_file.exists():
                compose_file = nbs_file

    if compose_file is None:
        beamline_file = beamline_pods_dir / "compose" / service / "docker-compose.yml"
        if verbose:
            print(f"Checking beamline file: {beamline_file}", flush=True)
        if beamline_file.exists():
            compose_file = beamline_file
        else:
            if verbose:
                print(f"Beamline file not found, checking nbs file", flush=True)
            nbs_file = nbs_pods_dir / "compose" / service / "docker-compose.yml"
            if nbs_file.exists():
                compose_file = nbs_file

    return compose_file


def get_compose_override(service, verbose=False):
    """
    Get the override compose file for a service.

    Parameters
    ----------
    service : str
        Service name

    Returns
    -------
    Path | None
        Path to override file, or None if not found
    """
    beamline_pods_dir = get_beamline_pods_dir()
    nbs_pods_dir = get_nbs_pods_dir()

    beamline_file = (
        beamline_pods_dir / "compose" / service / "docker-compose.override.yml"
    )
    if verbose:
        print(f"Checking beamline file: {beamline_file}", flush=True)
    if beamline_file.exists():
        return beamline_file

    nbs_file = nbs_pods_dir / "compose" / service / "docker-compose.override.yml"
    if verbose:
        print(f"Checking nbs file: {nbs_file}", flush=True)
    if nbs_file.exists():
        return nbs_file

    return None


def get_compose_development(service, verbose=False):
    """
    Get the development compose file for a service.

    Parameters
    ----------
    service : str
        Service name

    Returns
    -------
    Path | None
        Path to development file, or None if not found
    """
    beamline_pods_dir = get_beamline_pods_dir()
    nbs_pods_dir = get_nbs_pods_dir()

    beamline_file = (
        beamline_pods_dir / "compose" / service / "docker-compose.development.yml"
    )
    if verbose:
        print(f"Checking beamline file: {beamline_file}", flush=True)
    if beamline_file.exists():
        return beamline_file

    nbs_file = nbs_pods_dir / "compose" / service / "docker-compose.development.yml"
    if verbose:
        print(f"Checking nbs file: {nbs_file}", flush=True)
    if nbs_file.exists():
        return nbs_file

    return None


def build_compose_file_string(service, dev_mode=False, verbose=False):
    """
    Build the COMPOSE_FILE environment variable string.

    Parameters
    ----------
    service : str
        Service name
    dev_mode : bool
        Whether to include development file

    Returns
    -------
    str
        Colon-separated compose file paths

    Raises
    ------
    RuntimeError
        If no compose file found for service
    """
    compose_file = get_compose_file(service, verbose)
    if compose_file is None:
        raise RuntimeError(f"No compose file found for service {service}")

    compose_files = [compose_file]

    override_file = get_compose_override(service, verbose)
    if override_file:
        compose_files.append(override_file)

    if dev_mode:
        dev_file = get_compose_development(service, verbose)
        if dev_file:
            compose_files.append(dev_file)

    return ":".join(str(f) for f in compose_files)
