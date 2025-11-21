"""Configuration and path resolution."""

import os
from pathlib import Path


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
