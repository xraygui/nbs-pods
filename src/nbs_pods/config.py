"""Configuration and path resolution."""

import os
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def get_nbs_pods_dir():
    """
    Get the nbs-pods package data directory.

    Uses importlib.resources to find the installed package location,
    which works for both regular and editable installs.

    Returns
    -------
    Path
        nbs-pods package directory containing compose/, config/, etc.
    """
    try:
        from importlib import resources

        return Path(resources.files("nbs_pods"))
    except (ImportError, AttributeError):
        # Fallback for older Python or when resources.files not available
        # __file__ is nbs_pods/config.py, so parent is nbs_pods/
        return Path(__file__).parent


def get_beamline_pods_dir():
    """
    Get the beamline pods directory.

    Returns
    -------
    Path
        beamline pods directory, or nbs-pods dir if not set
    """
    beamline_pods_dir = os.getenv("BEAMLINE_PODS_DIR")
    if beamline_pods_dir:
        return Path(beamline_pods_dir).resolve()

    return get_nbs_pods_dir()


def _load_pods_toml(path):
    """
    Load a pods.toml file, returning an empty dict on failure.

    Parameters
    ----------
    path : Path
        Path to the TOML file.

    Returns
    -------
    dict
    """
    if tomllib is None or not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_beamline_pods_config():
    """
    Get the merged pods configuration for the current beamline.

    Loads ``compose/pods.toml`` from the nbs-pods package directory as the
    base, then deep-merges any ``compose/pods.toml`` found in the beamline
    pods directory on top.  Beamline values take precedence.

    Returns
    -------
    dict
        Merged configuration dictionary.
    """
    nbs_config = _load_pods_toml(get_nbs_pods_dir() / "compose" / "pods.toml")

    beamline_pods_dir = get_beamline_pods_dir()
    if beamline_pods_dir == get_nbs_pods_dir():
        return nbs_config

    beamline_config = _load_pods_toml(beamline_pods_dir / "compose" / "pods.toml")

    merged = dict(nbs_config)
    for service, service_cfg in beamline_config.items():
        if service in merged and isinstance(merged[service], dict):
            merged[service] = {**merged[service], **service_cfg}
        else:
            merged[service] = service_cfg

    return merged


def get_demo_services():
    """
    Get the list of services started by ``nbs-pods demo``.

    Reads ``demo_services`` from the merged pods configuration.  Beamlines
    can override this in their own ``compose/pods.toml``.

    Returns
    -------
    list[str]
        Ordered list of service names.
    """
    config = get_beamline_pods_config()
    return config.get("demo_services", ["bluesky-services", "gui", "queueserver", "sim", "viewer"])


def get_beamline_name():
    """
    Get the beamline name.

    Returns
    -------
    str
        beamline name, or 'demo' if not set
    """
    if beamline_name := os.getenv("BEAMLINE_NAME"):
        return beamline_name

    beamline_pods_dir = get_beamline_pods_dir()
    nbs_pods_dir = get_nbs_pods_dir()

    if beamline_pods_dir == nbs_pods_dir:
        return "demo"

    dir_name = beamline_pods_dir.name
    if dir_name.endswith("-pods"):
        return dir_name[:-5]

    return dir_name
