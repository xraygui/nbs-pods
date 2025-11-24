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


def copy_template_files(template_source, target_dir, beamline_name):
    """
    Copy template files and replace placeholders.

    Parameters
    ----------
    template_source : Path
        Source directory containing templates
    target_dir : Path
        Target directory to copy files to
    beamline_name : str
        Beamline name to use for replacements
    """
    target_dir.mkdir(parents=True, exist_ok=False)

    for item in template_source.iterdir():
        target_item = target_dir / item.name
        if item.is_dir():
            copy_template_files(item, target_item, beamline_name)
        else:
            target_item.parent.mkdir(parents=True, exist_ok=True)
            if item.suffix in (".toml", ".md", ".py", ".sh", ".yaml", ".yml"):
                content = item.read_text(encoding="utf-8")
                content = content.replace("${BEAMLINE_NAME}", beamline_name)
                target_item.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(item, target_item)


def make_scripts_executable(target_dir):
    """
    Make script files executable.

    Parameters
    ----------
    target_dir : Path
        Directory containing scripts
    """
    script_files = [target_dir / "src" / "beamline-pods" / "deploy.py"]
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


def create_beamline_pods(beamline_name, target_dir, init_git=True):
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

    Raises
    ------
    ValueError
        If beamline name is invalid or directory exists
    RuntimeError
        If template files cannot be found
    """
    validate_beamline_name(beamline_name)

    target_dir = Path(target_dir).resolve()
    if target_dir.exists():
        raise ValueError(f"Target directory already exists: {target_dir}")

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

    copy_template_files(template_dir, target_dir, beamline_name)
    make_scripts_executable(target_dir)

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
        "--no-git",
        action="store_true",
        help="Skip git repository initialization",
    )

    args = parser.parse_args()

    try:
        create_beamline_pods(
            args.beamline_name, args.target_dir, init_git=not args.no_git
        )
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
