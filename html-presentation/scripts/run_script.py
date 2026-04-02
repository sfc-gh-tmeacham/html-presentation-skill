#!/usr/bin/env python3
"""Cross-platform wrapper to run helper scripts inside an isolated virtual environment.

Automatically creates a venv in the scripts/ directory (if one doesn't exist),
installs required dependencies, and runs the specified Python script with all
provided arguments.

Prefers ``uv`` for fast venv creation and dependency installation.  Falls back
to the standard ``python -m venv`` + ``pip`` if uv is not available.

Works on macOS, Linux, and Windows.

Usage::

    python run_script.py <script.py> [args...]

Examples::

    python run_script.py resize_image.py input.png output.png --max-size 600
    python run_script.py img_to_base64.py logo.svg
    python run_script.py screenshot_to_slide.py capture.png --padding 16
    python run_script.py svg_optimize.py raw.svg clean.svg
    python run_script.py color_swap_svg.py logo.svg logo-light.svg --from-color "#000" --to-color "#fff"
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Dependencies required by the helper scripts (Pillow is the only external one).
DEPENDENCIES: list[str] = ["Pillow", "segno"]

SCRIPT_DIR: Path = Path(__file__).resolve().parent
VENV_DIR: Path = SCRIPT_DIR / ".venv"
DEPS_OK_SENTINEL: Path = VENV_DIR / ".deps_ok"


def _is_windows() -> bool:
    """Check if the current platform is Windows.

    Returns:
        True on Windows, False on macOS/Linux/other Unix.
    """
    return platform.system() == "Windows"


def _venv_python() -> Path:
    """Return the path to the Python interpreter inside the venv.

    Windows uses ``Scripts\\python.exe``, Unix uses ``bin/python``.

    Returns:
        Absolute path to the venv's Python binary.
    """
    if _is_windows():
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _venv_pip() -> Path:
    """Return the path to pip inside the venv.

    Returns:
        Absolute path to the venv's pip binary.
    """
    if _is_windows():
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def _has_command(name: str) -> bool:
    """Check whether a command is available on PATH.

    Args:
        name: The command name to look for (e.g. ``"uv"``).

    Returns:
        True if the command exists on PATH.
    """
    return shutil.which(name) is not None


def _run(cmd: list[str], check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess command with consistent error handling.

    Args:
        cmd: Command and arguments to execute.
        check: If True, raise on non-zero exit code.
        quiet: If True, suppress stdout/stderr.

    Returns:
        The completed process result.

    Raises:
        SystemExit: If the command fails and ``check`` is True.
    """
    try:
        kwargs: dict = {}
        if quiet:
            kwargs["stdout"] = subprocess.DEVNULL
            kwargs["stderr"] = subprocess.DEVNULL
        return subprocess.run(cmd, check=check, **kwargs)
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Error: Command failed (exit {exc.returncode}): {' '.join(cmd)}", file=sys.stderr)
        sys.exit(1)


def _create_venv_uv() -> None:
    """Create the venv and install dependencies using uv."""
    print("Creating virtual environment with uv...", file=sys.stderr)
    _run(["uv", "venv", str(VENV_DIR), "--quiet"])

    print(f"Installing dependencies: {', '.join(DEPENDENCIES)}...", file=sys.stderr)
    _run(["uv", "pip", "install", "--python", str(_venv_python())] + DEPENDENCIES + ["--quiet"])
    DEPS_OK_SENTINEL.touch()


def _create_venv_stdlib() -> None:
    """Create the venv using python's built-in venv module and pip."""
    print("uv not found — falling back to python -m venv...", file=sys.stderr)
    _run([sys.executable, "-m", "venv", str(VENV_DIR)])

    _run([str(_venv_pip()), "install", "--upgrade", "pip", "--quiet"])

    print(f"Installing dependencies: {', '.join(DEPENDENCIES)}...", file=sys.stderr)
    _run([str(_venv_pip()), "install"] + DEPENDENCIES + ["--quiet"])
    DEPS_OK_SENTINEL.touch()


def ensure_venv() -> None:
    """Ensure the virtual environment exists and has a working Python.

    Creates a new venv if one doesn't exist.  Prefers uv, falls back
    to the standard library.

    Raises:
        SystemExit: If neither uv nor python can create a venv, or if
            creation fails.
    """
    venv_python = _venv_python()

    # If the venv already exists and has a working Python, reuse it.
    if venv_python.is_file():
        return

    # Create a fresh venv.
    if _has_command("uv"):
        _create_venv_uv()
    else:
        _create_venv_stdlib()

    # Verify the venv was created successfully.
    if not venv_python.is_file():
        print(
            f"Error: Virtual environment creation failed — "
            f"{venv_python} not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Virtual environment ready at {VENV_DIR}", file=sys.stderr)


def ensure_deps() -> None:
    """Verify that required dependencies are importable; reinstall if not.

    Uses a sentinel file (``.deps_ok``) to skip the subprocess check on
    repeat invocations.  Only falls back to a live import check when the
    sentinel is absent.
    """
    if DEPS_OK_SENTINEL.is_file():
        return

    venv_python = str(_venv_python())

    result = subprocess.run(
        [venv_python, "-c", "import PIL; import segno"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        DEPS_OK_SENTINEL.touch()
        return

    print("Dependencies missing — reinstalling...", file=sys.stderr)
    if _has_command("uv"):
        _run(["uv", "pip", "install", "--python", venv_python] + DEPENDENCIES + ["--quiet"])
    else:
        _run([str(_venv_pip()), "install"] + DEPENDENCIES + ["--quiet"])
    DEPS_OK_SENTINEL.touch()


def list_available_scripts() -> list[str]:
    """List all .py helper scripts in the scripts/ directory (excluding this file).

    Returns:
        Sorted list of script filenames.
    """
    this_file = Path(__file__).name
    return sorted(
        f.name
        for f in SCRIPT_DIR.glob("*.py")
        if f.name != this_file and f.is_file()
    )


def resolve_target(script_name: str) -> Path:
    """Resolve the target script path from a bare name or relative/absolute path.

    Args:
        script_name: The script filename or path provided by the user.

    Returns:
        Absolute path to the target script.

    Raises:
        SystemExit: If the script cannot be found.
    """
    # Try as a bare name inside the scripts/ directory first.
    candidate = SCRIPT_DIR / script_name
    if candidate.is_file():
        return candidate

    # Try as-is (relative or absolute path).
    candidate = Path(script_name)
    if candidate.is_file():
        return candidate.resolve()

    print(f"Error: Script '{script_name}' not found in {SCRIPT_DIR}/", file=sys.stderr)
    available = list_available_scripts()
    if available:
        print("Available scripts:", file=sys.stderr)
        for name in available:
            print(f"  {name}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Parse arguments, ensure venv + deps, and exec the target script."""
    reinstall = False
    filtered_argv = [sys.argv[0]]
    remaining = sys.argv[1:]
    for i, arg in enumerate(remaining):
        if arg == "--reinstall":
            reinstall = True
        else:
            filtered_argv.append(arg)
            filtered_argv.extend(remaining[i + 1:])
            break

    if len(filtered_argv) < 2:
        print("Usage: python run_script.py [--reinstall] <script.py> [args...]", file=sys.stderr)
        print("", file=sys.stderr)
        available = list_available_scripts()
        if available:
            print("Available scripts:", file=sys.stderr)
            for name in available:
                print(f"  {name}", file=sys.stderr)
        sys.exit(1)

    if reinstall and VENV_DIR.exists():
        print(f"--reinstall: removing existing venv at {VENV_DIR}...", file=sys.stderr)
        shutil.rmtree(str(VENV_DIR))

    target_name = filtered_argv[1]
    target_path = resolve_target(target_name)
    script_args = filtered_argv[2:]

    # Some scripts (img_to_base64.py, svg_optimize.py, color_swap_svg.py) only
    # use the standard library and don't need Pillow.  We still run them inside
    # the venv for consistency and isolation.
    ensure_venv()
    ensure_deps()

    # Execute the script inside the venv, forwarding all remaining arguments.
    # Use os.execv on Unix for a clean process replacement; on Windows, use
    # subprocess.run since execv behaves differently there.
    venv_python = str(_venv_python())
    cmd = [venv_python, str(target_path)] + script_args

    if _is_windows():
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    else:
        # Replace the current process entirely — no zombie wrapper process.
        try:
            os.execv(venv_python, cmd)
        except OSError as exc:
            print(f"Error: Could not execute '{venv_python}': {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
