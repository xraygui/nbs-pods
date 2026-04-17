"""NBS Pods - Containerized NBS services management."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nbs-pods")
except PackageNotFoundError:
    __version__ = "0.0.0"
