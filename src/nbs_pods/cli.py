"""Command-line interface for nbs-pods."""

import argparse
import os
import subprocess
import sys

from nbs_pods.compose import build_compose_file_string
from nbs_pods.config import get_beamline_pods_dir, get_nbs_pods_dir
from nbs_pods.services import get_all_services


def setup_environment(beamline_pods_dir=None):
    """Setup environment variables."""
    env = os.environ.copy()
    env["HOST_UID"] = str(os.getuid())
    env["NBS_PODS_DIR"] = str(get_nbs_pods_dir())
    if beamline_pods_dir is not None:
        env["BEAMLINE_PODS_DIR"] = str(beamline_pods_dir)
    else:
        env["BEAMLINE_PODS_DIR"] = get_beamline_pods_dir()
    return env


def start_service(service, dev_mode=False, verbose=False):
    """
    Start a service using podman-compose.

    Parameters
    ----------
    service : str
        Service name
    dev_mode : bool
        Whether to start in development mode
    """
    mode_str = " (dev mode)" if dev_mode else ""
    print(f"Starting {service}{mode_str}...", flush=True)

    try:
        compose_file_string = build_compose_file_string(service, dev_mode, verbose)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    compose_files = compose_file_string.split(":")
    print("  Using compose files:")
    labels = ["(base)"]
    if len(compose_files) > 1:
        labels.append("(override)")
    if dev_mode and len(compose_files) > 2:
        labels.append("(development)")
    for i, compose_file in enumerate(compose_files):
        label = labels[i] if i < len(labels) else ""
        print(f"    - {compose_file} {label}", flush=True)

    env = setup_environment()
    env["COMPOSE_FILE"] = compose_file_string

    result = subprocess.run(
        ["podman-compose", "up", "-d"],
        env=env,
    )

    if result.returncode != 0:
        sys.exit(result.returncode)


def stop_service(service, verbose=False):
    """
    Stop a service using podman-compose.

    Parameters
    ----------
    service : str
        Service name
    """
    print(f"Stopping {service}...", flush=True)

    try:
        compose_file_string = build_compose_file_string(
            service, dev_mode=False, verbose=verbose
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    compose_files = compose_file_string.split(":")
    if len(compose_files) > 1:
        compose_file_string = ":".join(compose_files[:2])
    else:
        compose_file_string = compose_files[0]

    env = setup_environment()
    env["COMPOSE_FILE"] = compose_file_string

    result = subprocess.run(
        ["podman-compose", "down", "-v"],
        env=env,
    )

    if result.returncode != 0:
        sys.exit(result.returncode)


def cmd_start(args):
    """Handle start command."""
    base_services, beamline_services = get_all_services()
    all_services = base_services + beamline_services

    if not args.services and not args.dev:
        for service in all_services:
            start_service(service, dev_mode=False)
        return

    dev_services = args.dev
    verbose = args.verbose
    for item in args.services:
        if item not in all_services:
            print(f"Error: Unknown service '{item}'", file=sys.stderr)
            print_available_services()
            sys.exit(1)

        start_service(item, False, verbose)
    for item in dev_services:
        if item not in all_services:
            print(f"Error: Unknown service '{item}'", file=sys.stderr)
            print_available_services()
            sys.exit(1)
        start_service(item, True, verbose)


def cmd_stop(args):
    """Handle stop command."""
    base_services, beamline_services = get_all_services()
    all_services = base_services + beamline_services
    verbose = args.verbose
    if not args.services:
        for service in reversed(all_services):
            stop_service(service, verbose)
        return

    for service in args.services:
        if service not in all_services:
            print(f"Error: Unknown service '{service}'", file=sys.stderr)
            print_available_services()
            sys.exit(1)

        stop_service(service, verbose)


def cmd_demo(args):
    """Handle demo command."""
    demo_services = ["bluesky-services", "gui", "queueserver", "sim", "viewer"]
    for service in demo_services:
        start_service(service, dev_mode=False)


def cmd_list(args):
    """Handle list command."""
    print_available_services()


def print_available_services():
    """Print available services."""
    base_services, beamline_services = get_all_services()
    print("Available services:")
    print("Base services (can be overridden):")
    for service in base_services:
        print(f"  - {service}")
    if beamline_services:
        print("Beamline services:")
        for service in beamline_services:
            print(f"  - {service}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=("NBS Pods - Containerized NBS services management"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument(
        "services",
        nargs="*",
        help="Services to start (use --dev before service name for dev mode)",
    )
    start_parser.add_argument(
        "--dev", nargs="*", help="Start services in development mode", default=[]
    )
    start_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    start_parser.set_defaults(func=cmd_start)

    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument(
        "services",
        nargs="*",
        help="Services to stop",
    )
    stop_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    stop_parser.set_defaults(func=cmd_stop)

    demo_parser = subparsers.add_parser("demo", help="Start demo services")
    demo_parser.set_defaults(func=cmd_demo)

    list_parser = subparsers.add_parser("list", help="List available services")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
