"""Build pychonlang into a standalone (or onefile) executable via Nuitka.

Usage:
    python scripts/build/pyside.py                    # standalone folder build
    python scripts/build/pyside.py --onefile           # single-file build
    python scripts/build/pyside.py --skip-dotnet       # reuse an already-built bridge DLL
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # scripts/build/pyside.py -> repo root
ENTRY_POINT = ROOT / "src" / "app" / "__main__.py"
BRIDGE_PROJECT = ROOT / "src" / "bridge-net"
BRIDGE_BIN = BRIDGE_PROJECT / "bin" / "Release" / "net8.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Bundle into a single executable instead of a standalone folder.",
    )
    parser.add_argument(
        "--skip-dotnet",
        action="store_true",
        help="Skip the dotnet build step (use an already-built bridge DLL).",
    )
    return parser.parse_args()


def build_bridge() -> None:
    """Compile the PLGL bridge DLL via dotnet before Nuitka needs it."""
    command = ["dotnet", "build", str(BRIDGE_PROJECT), "-c", "Release"]
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


def base_options() -> list[str]:
    """Options shared by every build mode."""
    return [
        "--standalone",
        "--enable-plugin=pyside6",
        "--assume-yes-for-downloads",
        "--output-dir=build",
        "--output-filename=PyChonLang.exe",
    ]


def data_options() -> list[str]:
    """Non-Python files the app reads at runtime and must ship with the build."""
    return [
        # The compiled PLGL bridge (built above via `dotnet build`)
        f"--include-raw-dir={BRIDGE_BIN}={BRIDGE_BIN.relative_to(ROOT)}",
        # Language definitions and authoring docs shown inside the app
        "--include-data-dir=assets=assets",   # replaces the two md-*.css include-data-files lines
        "--include-data-dir=languages=languages",
        "--include-data-dir=docs=docs",
    ]


def onefile_options() -> list[str]:
    """Options that only apply when bundling into a single executable."""
    options = [
        "--onefile",
        "--onefile-tempdir-spec={TEMP}/pychonlang_{PID}",
    ]
    if sys.platform == "win32":
        options.append("--windows-console-mode=hide")
    return options


def build(onefile: bool, skip_dotnet: bool) -> None:
    if not skip_dotnet:
        build_bridge()

    if not BRIDGE_BIN.exists():
        sys.exit(
            f"Bridge DLL not found at {BRIDGE_BIN}\n"
            "Run without --skip-dotnet, or build it manually:\n"
            f"  dotnet build {BRIDGE_PROJECT} -c Release"
        )

    options = base_options() + data_options()
    if onefile:
        options += onefile_options()

    command = [sys.executable, "-m", "nuitka", *options, str(ENTRY_POINT)]

    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    args = parse_args()
    build(onefile=args.onefile, skip_dotnet=args.skip_dotnet)