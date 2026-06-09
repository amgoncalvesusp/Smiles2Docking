from __future__ import annotations

from pathlib import Path


def test_windows_spec_keeps_qt_runtime_files_next_to_exe() -> None:
    spec = Path("packaging/windows/smiles2docking.spec").read_text(encoding="utf-8")

    assert "pyinstaller_qt_runtime.py" in spec
    assert "packaging\" / \"qt.conf" in spec
    assert "qt_platforms_dir" in spec
    assert 'contents_directory="."' in spec
