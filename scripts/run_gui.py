from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
