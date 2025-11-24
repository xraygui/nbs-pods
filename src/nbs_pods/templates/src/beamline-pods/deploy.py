#!/usr/bin/env python3
"""Deployment script for beamline pods."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    beamline_pods_dir = script_dir.parent
    beamline_name = beamline_pods_dir.name.replace("-pods", "")

    os.environ["BEAMLINE_PODS_DIR"] = str(beamline_pods_dir.resolve())
    os.environ["BEAMLINE_NAME"] = beamline_name

    args = sys.argv[1:]
    if not args:
        args = ["start"]

    try:
        result = subprocess.run(["nbs-pods"] + args, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(
            "Error: nbs-pods CLI not found. Make sure nbs-pods is installed.",
            file=sys.stderr,
        )
        print("Run: pixi install", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
