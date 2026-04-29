from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _configure_qt_runtime() -> None:
    root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    pyside_root = root / "PySide6"
    plugin_root = pyside_root / "plugins"
    bundled_platforms_dir = root / "platforms"
    platforms_dir = bundled_platforms_dir if bundled_platforms_dir.exists() else plugin_root / "platforms"
    if not platforms_dir.exists():
        return
    if hasattr(os, "add_dll_directory") and pyside_root.exists():
        os.add_dll_directory(str(pyside_root))
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(root))
    os.environ["PATH"] = os.pathsep.join([str(root), str(pyside_root), os.environ.get("PATH", "")])
    os.environ["QT_PLUGIN_PATH"] = os.pathsep.join([str(plugin_root), str(root)])
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    os.environ["QT_QPA_PLATFORM"] = "windows"


_configure_qt_runtime()

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.utils.runtime import resolve_runtime_path


def main() -> int:
    app = QApplication(sys.argv)
    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    return app.exec()


def _load_app_icon() -> QIcon:
    candidates = (
        resolve_runtime_path("assets", "caffeine_icon.png"),
        resolve_runtime_path("assets", "caffeine_icon.ico"),
    )
    for candidate in candidates:
        if candidate.exists():
            return QIcon(str(candidate))
    return QIcon()


if __name__ == "__main__":
    raise SystemExit(main())
