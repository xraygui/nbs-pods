"""Command-line interface for nbs-pods."""

import argparse
import os
import subprocess
import sys
from copy import copy

from nbs_pods.compose import build_compose_file_string, get_service_variants
from nbs_pods.config import (
    get_beamline_pods_dir,
    get_demo_services,
    get_local_image_reg,
    get_nbs_pods_dir,
    get_presets,
)
from nbs_pods.services import get_all_services, discover_gui_services

gui_services = discover_gui_services()

DEFAULT_TEST_TASKS = {
    "queueserver": "qs-pytest",
}


def setup_environment(beamline_pods_dir=None):
    """
    Setup environment variables for podman-compose.

    Parameters
    ----------
    beamline_pods_dir : str or Path, optional
        Override for ``BEAMLINE_PODS_DIR``.

    Returns
    -------
    dict
        Environment mapping for subprocess calls.
    """
    env = os.environ.copy()
    env["HOST_UID"] = str(os.getuid())
    env["NBS_PODS_DIR"] = str(get_nbs_pods_dir())
    if beamline_pods_dir is not None:
        env["BEAMLINE_PODS_DIR"] = str(beamline_pods_dir)
    else:
        env["BEAMLINE_PODS_DIR"] = str(get_beamline_pods_dir())
    return env


def apply_image_options(args):
    """
    Apply ``--local`` / ``--image-reg`` / ``--image-tag`` to the process env.

    ``--local`` sets ``NBS_IMAGE_REG`` via ``get_local_image_reg()``
    (``localhost/<BEAMLINE_NAME>-`` when set, else ``localhost/nbs-``).
    ``--image-reg`` overrides that value when both are given.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments. Missing attributes are ignored.
    """
    if getattr(args, "local", False):
        os.environ["NBS_IMAGE_REG"] = get_local_image_reg()
    image_reg = getattr(args, "image_reg", None)
    if image_reg:
        os.environ["NBS_IMAGE_REG"] = image_reg
    image_tag = getattr(args, "image_tag", None)
    if image_tag:
        os.environ["NBS_IMAGE_TAG"] = image_tag
    if os.environ.get("NBS_IMAGE_REG") or os.environ.get("NBS_IMAGE_TAG"):
        print(
            "Using images: "
            f"{os.environ.get('NBS_IMAGE_REG', 'ghcr.io/xraygui/nbs-pods/')}"
            f"<name>:{os.environ.get('NBS_IMAGE_TAG', 'latest')}",
            flush=True,
        )


def add_image_option_args(parser):
    """
    Add shared image-selection flags to a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser to extend.
    """
    parser.add_argument(
        "--local",
        action="store_true",
        help=(
            "Use locally built images "
            "(localhost/<BEAMLINE_NAME>- if set, else localhost/nbs-)"
        ),
    )
    parser.add_argument(
        "--image-reg",
        metavar="PREFIX",
        help="Override NBS_IMAGE_REG (image name prefix before the service name)",
    )
    parser.add_argument(
        "--image-tag",
        metavar="TAG",
        help="Override NBS_IMAGE_TAG (default: latest)",
    )


def parse_service_token(token):
    """
    Parse a service token that may include a pixi task override.

    Parameters
    ----------
    token : str
        Either ``service`` or ``service=task``.

    Returns
    -------
    service : str
        Service name.
    task : str or None
        Pixi task name, or None to use the compose default.
    """
    if "=" not in token:
        return token, None
    service, task = token.split("=", 1)
    if not service or not task:
        raise ValueError(
            f"Invalid service token '{token}'; expected SERVICE or SERVICE=TASK"
        )
    return service, task


def print_compose_files(compose_file_string, override_keys):
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


def start_service(
    service,
    dev_mode=False,
    test_mode=False,
    hold_mode=False,
    ignore_override=False,
    verbose=False,
    task=None,
    foreground=False,
    teardown=False,
):
    """
    Start a service using podman-compose.

    Parameters
    ----------
    service : str
        Service name.
    dev_mode : bool
        Stack ``docker-compose.development.yml`` (mounts only).
    test_mode : bool
        Stack ``docker-compose.test.yml`` and run in the foreground.
    hold_mode : bool
        Stack ``docker-compose.hold.yml``.
    ignore_override : bool
        Skip ``docker-compose.override.yml``.
    verbose : bool
        Print compose file resolution details.
    task : str or None
        Pixi task name exported as ``NBS_PIXI_TASK``.
    foreground : bool
        Run ``podman-compose up`` without ``-d``.
    teardown : bool
        After a foreground run, tear the service down.
    """
    parts = []
    if dev_mode:
        parts.append("dev mounts")
    if test_mode:
        parts.append("test")
    if task:
        parts.append(f"task={task}")
    if foreground:
        parts.append("foreground")
    mode_str = f" ({', '.join(parts)})" if parts else ""
    print(f"Starting {service}{mode_str}...", flush=True)

    override_keys = []
    variant_keys = get_service_variants(service)
    if len(variant_keys) > 0:
        override_keys.extend(variant_keys)
    if not ignore_override:
        override_keys.append("override")
    if dev_mode:
        override_keys.append("development")
    if test_mode:
        override_keys.append("test")
    if hold_mode:
        override_keys.append("hold")

    try:
        compose_file_string = build_compose_file_string(
            service, verbose, gui_services, override_keys
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print_compose_files(compose_file_string, override_keys)

    env = setup_environment()
    env["COMPOSE_FILE"] = compose_file_string
    if task:
        env["NBS_PIXI_TASK"] = task
    else:
        env.pop("NBS_PIXI_TASK", None)

    run_foreground = foreground or test_mode
    command = ["podman-compose", "up"]
    if not run_foreground:
        command.append("-d")
    else:
        command.append("--abort-on-container-exit")
        command.extend(["--exit-code-from", service])
    result = subprocess.run(command, env=env)

    if teardown and run_foreground:
        print(f"Tearing down {service}...", flush=True)
        subprocess.run(["podman-compose", "down", "-v"], env=env)

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

    override_keys = []
    variant_keys = get_service_variants(service)
    if len(variant_keys) > 0:
        override_keys.extend(variant_keys)

    try:
        compose_file_string = build_compose_file_string(
            service, verbose=verbose, gui_services=gui_services, override_keys=override_keys
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print_compose_files(compose_file_string, override_keys)

    env = setup_environment()
    env["COMPOSE_FILE"] = compose_file_string
    env.pop("NBS_PIXI_TASK", None)

    result = subprocess.run(
        ["podman-compose", "down", "-v"],
        env=env,
    )

    if result.returncode != 0:
        sys.exit(result.returncode)
    return result


def _resolve_start_token(token, *, test_mode=False):
    """
    Resolve a CLI/preset token into a service name and pixi task.

    Parameters
    ----------
    token : str
        ``service`` or ``service=task``.
    test_mode : bool
        If True and no task is given, use ``DEFAULT_TEST_TASKS``.

    Returns
    -------
    service : str
    task : str or None
    """
    try:
        service, task = parse_service_token(token)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    if test_mode and task is None:
        task = DEFAULT_TEST_TASKS.get(service)
    return service, task


def _ensure_known_service(service, all_services):
    if service not in all_services:
        print(f"Error: Unknown service '{service}'", file=sys.stderr)
        print_available_services()
        sys.exit(1)


def cmd_start(args):
    """Handle start command."""
    base_services, beamline_services = get_all_services()
    all_services = base_services + beamline_services
    dev_mode = bool(getattr(args, "dev", False))

    if not args.services and not args.test:
        for service in all_services:
            start_service(service, dev_mode=dev_mode)
        return

    verbose = args.verbose
    hold_mode = args.hold
    ignore_override = args.ignore_override
    foreground = args.foreground
    teardown = args.teardown

    for item in args.services:
        service, task = _resolve_start_token(item)
        _ensure_known_service(service, all_services)
        start_service(
            service,
            dev_mode=dev_mode,
            task=task,
            verbose=verbose,
            ignore_override=ignore_override,
            hold_mode=hold_mode,
            foreground=foreground,
            teardown=teardown,
        )
    for item in args.test:
        service, task = _resolve_start_token(item, test_mode=True)
        _ensure_known_service(service, all_services)
        start_service(
            service,
            dev_mode=dev_mode,
            test_mode=True,
            task=task,
            verbose=verbose,
            ignore_override=ignore_override,
            hold_mode=hold_mode,
            foreground=foreground,
            teardown=teardown,
        )


def cmd_restart(args):
    stop_args = copy(args)
    stop_tokens = list(getattr(args, "services", []) or [])
    stop_tokens += getattr(args, "test", []) or []
    stop_args.services = []
    for token in stop_tokens:
        service, _ = _resolve_start_token(token)
        stop_args.services.append(service)
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

    for token in args.services:
        service, _ = _resolve_start_token(token)
        _ensure_known_service(service, all_services)
        stop_service(service, verbose)


def cmd_demo(args):
    """Handle demo command."""
    services = get_demo_services()
    print(f"Starting demo services: {services}")
    for service in services:
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


def parse_preset_services(service_list):
    """
    Parse a preset service list into per-service start specs.

    Tokens ``--dev`` and ``--test`` are sticky flags for subsequent
    services (combinable). ``--normal`` clears both flags.

    Parameters
    ----------
    service_list : list[str]
        Mixed list of service tokens and mode flags.

    Returns
    -------
    list[tuple[str, bool, bool]]
        Each entry is ``(token, dev_mode, test_mode)``.
    """
    entries = []
    dev_mode = False
    test_mode = False
    for item in service_list:
        if item == "--dev":
            dev_mode = True
        elif item == "--test":
            test_mode = True
        elif item == "--normal":
            dev_mode = False
            test_mode = False
        else:
            entries.append((item, dev_mode, test_mode))
    return entries


def make_cmd_preset(preset_name):
    """
    Return a command handler that starts the named preset.

    Parameters
    ----------
    preset_name : str
        Key in the ``[presets]`` table of ``pods.toml``.

    Returns
    -------
    callable
        Argparse command handler accepting an ``args`` namespace.
    """

    def cmd_preset(args):
        presets = get_presets()
        service_list = presets[preset_name]
        entries = parse_preset_services(service_list)
        verbose = getattr(args, "verbose", False)
        foreground = getattr(args, "foreground", False)
        teardown = getattr(args, "teardown", False)
        print(f"Running preset '{preset_name}'...")
        for token, dev_mode, test_mode in entries:
            service, task = _resolve_start_token(token, test_mode=test_mode)
            start_service(
                service,
                dev_mode=dev_mode,
                test_mode=test_mode,
                task=task,
                verbose=verbose,
                foreground=foreground,
                teardown=teardown,
            )

    return cmd_preset


def cmd_list_presets(args):
    """Handle presets command — list available presets."""
    presets = get_presets()
    if not presets:
        print("No presets defined.")
        return
    print("Available presets:")
    for name, service_list in presets.items():
        print(f"  {name}: {service_list}")


def add_run_mode_args(parser):
    """
    Add foreground/teardown flags shared by start and presets.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser to extend.
    """
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="Run services in the foreground (implied by --test)",
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        help="Tear down foreground services after they exit",
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=("NBS Pods - Containerized NBS services management"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    image_options = argparse.ArgumentParser(add_help=False)
    add_image_option_args(image_options)

    run_mode_options = argparse.ArgumentParser(add_help=False)
    add_run_mode_args(run_mode_options)

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    start_parser = subparsers.add_parser(
        "start",
        parents=[image_options, run_mode_options],
        help="Start services",
    )
    start_parser.add_argument(
        "services",
        nargs="*",
        help=(
            "Services to start as SERVICE or SERVICE=PIXI_TASK "
            "(e.g. queueserver=qs-dev)"
        ),
    )
    start_parser.add_argument(
        "--dev",
        action="store_true",
        help=(
            "Stack development mounts for all services in this command "
            "(combinable with --test)"
        ),
    )
    start_parser.add_argument(
        "--test",
        nargs="*",
        help=(
            "Services with test mounts, foreground run, and default test task "
            "(queueserver -> qs-pytest unless SERVICE=TASK is given). "
            "Combine with --dev for development mounts on the same services."
        ),
        default=[],
    )
    start_parser.add_argument(
        "--hold",
        action="store_true",
        help="Do not run any command, but hold all services after starting",
    )
    start_parser.add_argument(
        "--ignore-override",
        action="store_true",
        help="Ignore override files",
    )
    start_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    start_parser.set_defaults(func=cmd_start)

    restart_parser = subparsers.add_parser(
        "restart", parents=[image_options, run_mode_options], help="Restart services"
    )
    restart_parser.add_argument(
        "services",
        nargs="*",
        help="Services to restart (SERVICE or SERVICE=PIXI_TASK)",
    )
    restart_parser.add_argument(
        "--dev",
        action="store_true",
        help="Stack development mounts for all services in this command",
    )
    restart_parser.add_argument(
        "--test", nargs="*", help="Restart services in test mode", default=[]
    )
    restart_parser.add_argument(
        "--hold",
        action="store_true",
        help="Do not run any command, but hold all services after starting",
    )
    restart_parser.add_argument(
        "--ignore-override",
        action="store_true",
        help="Ignore override files",
    )
    restart_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    restart_parser.set_defaults(func=cmd_restart)

    stop_parser = subparsers.add_parser(
        "stop", parents=[image_options], help="Stop services"
    )
    stop_parser.add_argument(
        "services",
        nargs="*",
        help="Services to stop",
    )
    stop_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    stop_parser.set_defaults(func=cmd_stop)

    list_parser = subparsers.add_parser("list", help="List available services")
    list_parser.set_defaults(func=cmd_list)

    presets_parser = subparsers.add_parser("presets", help="List available presets")
    presets_parser.set_defaults(func=cmd_list_presets)

    for preset_name, service_list in get_presets().items():
        preset_parser = subparsers.add_parser(
            preset_name,
            parents=[image_options, run_mode_options],
            help=f"Run preset '{preset_name}': {service_list}",
        )
        preset_parser.add_argument(
            "-v", "--verbose", action="store_true", help="Verbose output"
        )
        preset_parser.set_defaults(func=make_cmd_preset(preset_name))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    apply_image_options(args)
    args.func(args)


if __name__ == "__main__":
    main()
