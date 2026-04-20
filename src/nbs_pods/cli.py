"""Command-line interface for nbs-pods."""

import argparse
import os
import subprocess
import sys
from copy import copy

from nbs_pods.compose import build_compose_file_string
from nbs_pods.config import get_beamline_pods_dir, get_nbs_pods_dir
from nbs_pods.services import get_all_services, discover_gui_services

gui_services = discover_gui_services()

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


def start_service(service, dev_mode=False, test_mode=False, hold_mode=False, ignore_override=False, verbose=False):
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

    override_keys = []
    if not ignore_override:
        override_keys.append("override")
    if dev_mode:
        override_keys.append("development")
    if test_mode:
        override_keys.append("test")
    if hold_mode:
        override_keys.append("hold")

    try:
        compose_file_string = build_compose_file_string(service, verbose, gui_services, override_keys)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    compose_files = compose_file_string.split(":")
    print("  Using compose files:")
    labels = ["(base)"]
    for compose_file in compose_files[1:]:
        compose_name = os.path.basename(compose_file)
        label = ""
        for key in override_keys:
            if compose_name == f"docker-compose.{key}.yml":
                label = f"({key})"
                break
        labels.append(label)

    for i, compose_file in enumerate(compose_files):
        label = labels[i] if i < len(labels) else ""
        print(f"    - {compose_file} {label}", flush=True)

    env = setup_environment()
    env["COMPOSE_FILE"] = compose_file_string

    command = ["podman-compose", "up"]
    if not test_mode:
        command.append("-d")
    else:
        command.append("--abort-on-container-exit")
        command.extend(["--exit-code-from", "main"])
    result = subprocess.run(command, env=env)

    if result.returncode != 0:
        sys.exit(result.returncode)
    return result


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
            service, verbose=verbose, gui_services=gui_services
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
    return result


def cmd_start(args):
    """Handle start command."""
    base_services, beamline_services = get_all_services()
    all_services = base_services + beamline_services

    if not args.services and not args.dev and not args.test:
        for service in all_services:
            start_service(service, dev_mode=False)
        return

    dev_services = args.dev
    test_services = args.test
    verbose = args.verbose
    hold_mode = args.hold
    ignore_override = args.ignore_override
    for item in args.services:
        if item not in all_services:
            print(f"Error: Unknown service '{item}'", file=sys.stderr)
            print_available_services()
            sys.exit(1)

        start_service(item, verbose=verbose, ignore_override=ignore_override, hold_mode=hold_mode)
    for item in dev_services:
        if item not in all_services:
            print(f"Error: Unknown service '{item}'", file=sys.stderr)
            print_available_services()
            sys.exit(1)
        start_service(item, dev_mode=True, verbose=verbose, ignore_override=ignore_override, hold_mode=hold_mode)
    for item in test_services:
        if item not in all_services:
            print(f"Error: Unknown service '{item}'", file=sys.stderr)
            print_available_services()
            sys.exit(1)
        start_service(item, test_mode=True, verbose=verbose, ignore_override=ignore_override, hold_mode=hold_mode)


def cmd_restart(args):
    stop_args = copy(args)
    stop_args.services += getattr(args, "dev", [])
    stop_args.services += getattr(args, "test", [])
    print(f"Restarting {stop_args.services}")

    cmd_stop(stop_args)
    cmd_start(args)


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
        "--dev", nargs="*", help="Services to start in development mode", default=[]
    )
    start_parser.add_argument("--test", nargs="*", help="Services to start in test mode", default=[])
    start_parser.add_argument("--hold", action="store_true", help="Do not run any command, but hold all services after starting")
    start_parser.add_argument("--ignore-override", action="store_true", help="Ignore override files")
    start_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    start_parser.set_defaults(func=cmd_start)

    restart_parser = subparsers.add_parser("restart", help="Restart services")
    restart_parser.add_argument(
        "services",
        nargs="*",
        help="Services to restart (use --dev before service name for dev mode)",
    )
    restart_parser.add_argument(
        "--dev", nargs="*", help="Restart services in development mode", default=[]
    )
    restart_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    restart_parser.set_defaults(func=cmd_restart)

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
