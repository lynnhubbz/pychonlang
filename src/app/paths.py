"""Resolves bundled-resource paths correctly whether running from source or compiled."""
import sys
from pathlib import Path


def app_root() -> Path:
    if "__compiled__" in globals():          # true only inside a Nuitka-compiled module
        return Path(sys.argv[0]).resolve().parent
    # repo_root/src/app/paths.py -> repo_root
    return Path(__file__).resolve().parent.parent.parent