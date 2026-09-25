"""Loads PLGL (C#) into Python via pythonnet."""
import json
from pathlib import Path
from pythonnet import load

BIN = Path(__file__).parent / "csharp" / "bin" / "Release" / "net8.0"
load("coreclr", runtime_config=str(BIN / "PLGLBridge.runtimeconfig.json"))

import clr  # noqa: E402
clr.AddReference(str(BIN / "PLGLBridge.dll"))   #type:ignore
from PLGLBridge import Bridge  # noqa: E402     #type:ignore


def generate(lang: dict, text: str) -> str:
    return Bridge.Generate(json.dumps(lang, ensure_ascii=False), text)
