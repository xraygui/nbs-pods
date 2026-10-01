"""Package creation utilities for beamline pods."""

import os
import re
import shutil
import subprocess
from pathlib import Path
import argparse
import sys

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources

try:
    from importlib.metadata import PackageNotFoundError, version as package_version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version as package_version


def validate_beamline_name(name):
    """
    Validate beamline name format.

    Parameters
    ----------
    name : str
        Beamline name to validate

    Raises
    ------
    ValueError
        If name is invalid
    """
    if not name:
        raise ValueError("Beamline name cannot be empty")
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            "Beamline name must contain only alphanumeric characters, "
            "hyphens, and underscores"
        )


def is_clean_release_version(version):
    """
    Return True if version is an exact X.Y.Z release string.

    Parameters
    ----------
    version : str
        Version string to check

    Returns
    -------
    bool
    """
    return re.fullmatch(r"\d+\.\d+\.\d+", version) is not None


def format_nbs_pods_pin(release):
    """
    Format a PyPI-compatible nbs-pods version pin.

    For ``0.Y.Z`` pins the next minor as the exclusive upper bound.
    For ``X.Y.Z`` with ``X >= 1`` pins the next major.

    Parameters
    ----------
    release : str
        Clean release version (e.g. ``"0.2.6"``)

    Returns
    -------
    str
        Pin string such as ``">=0.2.6, <0.3"``
    """
    if not is_clean_release_version(release):
        raise ValueError(f"Expected clean X.Y.Z release version, got {release!r}")
    major_s, minor_s, _patch_s = release.split(".")
    major = int(major_s)
    minor = int(minor_s)
    if major == 0:
        upper = f"0.{minor + 1}"
    else:
        upper = str(major + 1)
    return f">={release}, <{upper}"


def _nearest_git_release_tag():
    """
    Return the nearest annotated/lightweight git tag without the leading ``v``.

    Returns
    -------
    str or None
    """
    search_roots = [Path(__file__).resolve().parent]
    try:
        search_roots.insert(0, Path(resources.files("nbs_pods")).resolve())
    except (TypeError, FileNotFoundError, AttributeError):
        pass

    seen = set()
    for start in search_roots:
        for directory in [start, *start.parents]:
            directory = directory.resolve()
            if directory in seen:
                continue
            seen.add(directory)
            if not (directory / ".git").exists():
                continue
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return None
            tag = result.stdout.strip()
            if tag.startswith("v"):
                tag = tag[1:]
            return tag if is_clean_release_version(tag) else None
    return None


def resolve_nbs_pods_release_version():
    """
    Resolve the nbs-pods release version to pin in a new child package.

    Prefers the nearest git release tag when running from an nbs-pods
    checkout (so local/dev installs are not pinned as releases). Otherwise
    uses a clean installed package version from metadata.

    Returns
    -------
    tuple[str, bool]
        ``(release_version, used_git_fallback)``

    Raises
    ------
    RuntimeError
        If no suitable release version can be determined
    """
    tag = _nearest_git_release_tag()
    installed = None
    try:
        installed = package_version("nbs-pods")
    except PackageNotFoundError:
        installed = None

    if tag:
        used_git_fallback = not (
            installed is not None
            and is_clean_release_version(installed)
            and installed == tag
        )
        return tag, used_git_fallback

    if installed and is_clean_release_version(installed):
        return installed, False

    if installed:
        public = installed.split("+", 1)[0]
        public = public.split(".dev", 1)[0]
        if is_clean_release_version(public):
            return public, True

    raise RuntimeError(
        "Could not determine an nbs-pods release version to pin. "
        "Install a released nbs-pods or run create from a git checkout with tags."
    )


def copy_template_files(template_source, target_dir, replacements):
    """
    Copy template files and replace placeholders.

    Parameters
    ----------
    template_source : Path
        Source directory containing templates
    target_dir : Path
        Target directory to copy files to
    replacements : dict[str, str]
        Placeholder string to replacement value mapping
    """
    target_dir.mkdir(parents=True, exist_ok=False)
    beamline_name = replacements["${BEAMLINE_NAME}"]

    for item in template_source.iterdir():
        if item.name == "beamline_pods":
            target_item_name = f"{beamline_name}_pods"
        else:
            target_item_name = item.name
        target_item = target_dir / target_item_name
        if item.is_dir():
            copy_template_files(item, target_item, replacements)
        else:
            target_item.parent.mkdir(parents=True, exist_ok=True)
            if item.suffix in (".toml", ".md", ".py", ".sh", ".yaml", ".yml"):
                content = item.read_text(encoding="utf-8")
                for placeholder, value in replacements.items():
                    content = content.replace(placeholder, value)
                target_item.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(item, target_item)


def make_scripts_executable(target_dir, beamline_name):
    """
    Make script files executable.

    Parameters
    ----------
    target_dir : Path
        Directory containing scripts
    beamline_name : str
        Beamline name to construct correct path
    """
    beamline_pods_name = f"{beamline_name}_pods"
    script_files = [
        target_dir / "src" / beamline_pods_name / "deploy.py",
    ]
    for script_file in script_files:
        if script_file.exists():
            os.chmod(script_file, 0o755)


def init_git_repo(target_dir):
    """
    Initialize git repository and create initial commit.

    Parameters
    ----------
    target_dir : Path
        Directory to initialize git in
    """
    subprocess.run(["git", "init"], cwd=target_dir, check=True)
    subprocess.run(["git", "add", "."], cwd=target_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit from nbs-pods template"],
        cwd=target_dir,
        check=True,
    )


def create_beamline_pods(beamline_name, target_dir, init_git=True, dry_run=False):
    """
    Create a new beamline pods package from templates.

    Parameters
    ----------
    beamline_name : str
        Name of the beamline
    target_dir : Path | str
        Target directory where package will be created
    init_git : bool
        Whether to initialize git repository (default: True)
    dry_run : bool
        If True, print what would be created and return without writing files

    Raises
    ------
    ValueError
        If beamline name is invalid or directory exists
    RuntimeError
        If template files cannot be found or version cannot be resolved
    """
    validate_beamline_name(beamline_name)

    target_dir = Path(target_dir).resolve() / f"{beamline_name}-pods"
    if target_dir.exists():
        raise ValueError(f"Target directory already exists: {target_dir}")

    release, used_git_fallback = resolve_nbs_pods_release_version()
    nbs_pods_pin = format_nbs_pods_pin(release)

    try:
        nbs_pods_dir = Path(resources.files("nbs_pods"))
        template_dir = nbs_pods_dir / "templates"
        if not template_dir.exists():
            raise RuntimeError(
                f"Template directory not found: {template_dir}. "
                "Make sure nbs-pods is properly installed."
            )
    except (ImportError, AttributeError, TypeError):
        fallback_path = Path(__file__).parent.parent / "templates"
        if fallback_path.exists():
            template_dir = fallback_path
        else:
            raise RuntimeError(
                "Template directory not found. "
                "Make sure nbs-pods is properly installed."
            )

    if dry_run:
        print(f"Dry run: Would create {beamline_name}-pods package in {target_dir}")
        print(f"Dry run: Would pin nbs-pods = \"{nbs_pods_pin}\"")
        return

    replacements = {
        "${BEAMLINE_NAME}": beamline_name,
        "${NBS_PODS_PIN}": nbs_pods_pin,
    }
    copy_template_files(template_dir, target_dir, replacements)
    make_scripts_executable(target_dir, beamline_name)

    if used_git_fallback:
        print(
            f"⚠ Pinning nbs-pods from git tag as \"{nbs_pods_pin}\" "
            f"(installed package metadata was not a matching clean release)"
        )
    else:
        print(f"✓ Pinning nbs-pods = \"{nbs_pods_pin}\"")

    if init_git:
        try:
            init_git_repo(target_dir)
            print("✓ Initialized git repository")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"⚠ Warning: Could not initialize git repository: {e}")

    print(f"\n✓ Successfully created {beamline_name}-pods package " f"in {target_dir}")
    print("\nNext steps:")
    print(f"  1. cd {target_dir}")
    print("  2. Edit config/ipython/profile_default/startup/beamline.toml")
    print("  3. Edit config/ipython/profile_default/startup/devices.toml")
    print("  4. Add beamline-specific services in compose/beamline/")
    print("  5. Customize core services in compose/override/")
    print("  6. Run 'pixi install' to install dependencies")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new beamline pods package from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "beamline_name",
        help="Name of the beamline (alphanumeric, hyphens, underscores only)",
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Target directory where the package will be created",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run the creation process",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git repository initialization",
    )

    args = parser.parse_args()

    try:
        create_beamline_pods(
            args.beamline_name,
            args.target_dir,
            init_git=not args.no_git,
            dry_run=args.dry_run,
        )
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
