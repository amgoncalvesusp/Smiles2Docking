from __future__ import annotations

import os
import sys
from pathlib import Path


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))


bundle_root = _bundle_root()
pyside_root = bundle_root / "PySide6"
plugin_root = pyside_root / "plugins"
bundled_platforms_dir = bundle_root / "platforms"
platforms_dir = bundled_platforms_dir if bundled_platforms_dir.exists() else plugin_root / "platforms"

if platforms_dir.exists():
    if hasattr(os, "add_dll_directory") and pyside_root.exists():
        os.add_dll_directory(str(pyside_root))
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(bundle_root))
    os.environ["PATH"] = os.pathsep.join(
        [str(bundle_root), str(pyside_root), os.environ.get("PATH", "")]
    )
    os.environ["QT_PLUGIN_PATH"] = os.pathsep.join([str(plugin_root), str(bundle_root)])
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    os.environ["QT_QPA_PLATFORM"] = "windows"
