from __future__ import annotations

import os
import sys
from pathlib import Path


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))


bundle_root = _bundle_root()
pyside_root = bundle_root / "PySide6"
plugin_root = pyside_root / "plugins"
platforms_dir = plugin_root / "platforms"

if platforms_dir.exists():
    if hasattr(os, "add_dll_directory") and pyside_root.exists():
        os.add_dll_directory(str(pyside_root))
    os.environ["PATH"] = str(pyside_root) + os.pathsep + os.environ.get("PATH", "")
    os.environ["QT_PLUGIN_PATH"] = str(plugin_root)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    os.environ["QT_QPA_PLATFORM"] = "windows"
