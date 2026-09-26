"""Build pychonlang into a standalone (or onefile) executable via Nuitka.

Usage:
    python scripts/build/main.py                    # standalone folder build
    python scripts/build/main.py --onefile           # single-file build
    python scripts/build/main.py --skip-dotnet       # reuse an already-built bridge DLL
"""
import argparse
import subprocess
import sys

from _core import ROOT, base_options, data_options, onefile_options, run_nuitka

ENTRY_POINT = ROOT / "src" / "app" / "__main__.py"
BRIDGE_PROJECT = ROOT / "src" / "bridge" / "net"
BRIDGE_BIN = BRIDGE_PROJECT / "bin" / "Release" / "net8.0"

JS_ENTRY = ROOT / "src" / "bridge" / "js" / "entry.js"
JS_DIST = ROOT / "src" / "bridge" / "js" / "dist"




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
    parser.add_argument(
        "--skip-js",
        action="store_true",
        help="Skip the esbuild step (use an already-built JS bundle).",
    )
    return parser.parse_args()


def build_net() -> None:
    """Compile the PLGL bridge DLL via dotnet before Nuitka needs it."""
    command = ["dotnet", "build", str(BRIDGE_PROJECT), "-c", "Release"]
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)

def build_js() -> None:
    """Bundle ConlangEngine modules into one file for mini-racer."""
    command = [
        "npx", "esbuild", str(JS_ENTRY), "--bundle", "--format=iife",
        "--global-name=CE", f"--outfile={JS_DIST / 'ce-bundle.js'}", "--loader:.jsx=jsx",
    ]
    print("Running:", " ".join(command))
    subprocess.run(command, check=True, shell=(sys.platform == "win32"))  # npx is npx.cmd on Windows


def build(onefile: bool, skip_dotnet: bool, skip_js: bool) -> None:
    if not skip_dotnet:
        build_net()
    if not skip_js:
        build_js()

    if not BRIDGE_BIN.exists():
        sys.exit(
            f"Bridge DLL not found at {BRIDGE_BIN}\n"
            "Run without --skip-dotnet, or build it manually:\n"
            f"  dotnet build {BRIDGE_PROJECT} -c Release"
        )

    options = base_options("PyChonLang") + data_options([
        (str(BRIDGE_BIN), str(BRIDGE_BIN.relative_to(ROOT))),
        "assets",
        "languages",
        "docs",
        "src/bridge/js/dist",
    ])
    options += ["--include-package-data=py_mini_racer"]   # ← fix 1: mini-racer's data file
    if onefile:
        options += onefile_options(tempdir_tag="pychonlang")

    run_nuitka(ENTRY_POINT, options)


if __name__ == "__main__":
    args = parse_args()
    build(onefile=args.onefile, skip_dotnet=args.skip_dotnet, skip_js=args.skip_js)
