"""Build pychonlang into a standalone (or onefile) executable via Nuitka.

Usage:
    python scripts/build/pyside.py                    # standalone folder build
    python scripts/build/pyside.py --onefile           # single-file build
    python scripts/build/pyside.py --skip-dotnet       # reuse an already-built bridge DLL
"""
import argparse
import subprocess
import sys

from _core import ROOT, base_options, data_options, onefile_options, run_nuitka

ENTRY_POINT = ROOT / "src" / "app" / "__main__.py"
BRIDGE_PROJECT = ROOT / "src" / "bridge" / "net"
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


def build(onefile: bool, skip_dotnet: bool) -> None:
    if not skip_dotnet:
        build_bridge()

    if not BRIDGE_BIN.exists():
        sys.exit(
            f"Bridge DLL not found at {BRIDGE_BIN}\n"
            "Run without --skip-dotnet, or build it manually:\n"
            f"  dotnet build {BRIDGE_PROJECT} -c Release"
        )

    options = base_options("PyChonLang") + data_options([
        # The compiled PLGL bridge (built above via `dotnet build`)
        (str(BRIDGE_BIN), str(BRIDGE_BIN.relative_to(ROOT))),
        "assets",
        "languages",
        "docs",
        "src/js/dist",
    ])
    if onefile:
        options += onefile_options(tempdir_tag="pychonlang")

    run_nuitka(ENTRY_POINT, options)


if __name__ == "__main__":
    args = parse_args()
    build(onefile=args.onefile, skip_dotnet=args.skip_dotnet)
