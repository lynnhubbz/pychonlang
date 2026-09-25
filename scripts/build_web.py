import subprocess
import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "src" / "ConlangEngine"
DIST = ENGINE / "dist"
NPM = "npm.cmd" if sys.platform == "win32" else "npm"
BUILD_ENV = os.environ | {"VITE_OFFLINE_DESKTOP": "true"}


def main() -> None:
    if not (ENGINE / "package.json").is_file():
        raise FileNotFoundError(
            f"ConlangEngine submodule is not initialized: {ENGINE}"
        )

    print("Installing JavaScript dependencies...")
    subprocess.run([NPM, "ci"], cwd=ENGINE, check=True, env=BUILD_ENV)

    print("Building ConlangEngine...")
    subprocess.run([NPM, "run", "build"], cwd=ENGINE, check=True, env=BUILD_ENV)

    if not (DIST / "index.html").is_file():
        raise RuntimeError(f"The Vite build did not create {DIST / 'index.html'}")

    print(f"Web build ready: {DIST}")


if __name__ == "__main__":
    main()
