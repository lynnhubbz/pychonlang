"""Shared Nuitka build helpers.

Not run directly — see pyside.py (pychonlang), which both import from here.
"""
import subprocess
import sys
from pathlib import Path

# scripts/build/_core.py -> repo root
ROOT = Path(__file__).resolve().parent.parent.parent


def base_options(app_name: str) -> list[str]:
    """Options shared by every build, every target."""
    return [
        "--standalone",
        "--enable-plugin=pyside6",
        "--assume-yes-for-downloads",
        "--output-dir=build",
        f"--output-filename={app_name}.exe",
    ]


def data_options(items: list) -> list[str]:
    """Bundle non-Python files/folders the app reads at runtime.

    Each item is either "name" (bundled under the same relative path)
    or a ("source", "dest") tuple when the destination name differs
    from the source, e.g. ("src/ConlangEngine/dist", "web").
    """
    options = []
    for item in items:
        source, dest = item if isinstance(item, tuple) else (item, item)
        options.append(f"--include-data-dir={source}={dest}")
    return options


def onefile_options(tempdir_tag: str) -> list[str]:
    """Options that only apply when bundling into a single executable.

    tempdir_tag namespaces the extraction folder (e.g. "pychonlang")
    so two onefile builds never collide in %TEMP%.
    """
    options = [
        "--onefile",
        f"--onefile-tempdir-spec={{TEMP}}/{tempdir_tag}_{{PID}}",
    ]
    if sys.platform == "win32":
        options.append("--windows-console-mode=hide")
    return options


def run_nuitka(entry_point: Path, options: list[str]) -> None:
    command = [sys.executable, "-m", "nuitka", *options, str(entry_point)]
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)
