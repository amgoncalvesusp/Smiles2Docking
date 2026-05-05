from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from src.utils import runtime


@contextmanager
def workspace_tmp_dir() -> Path:
    root = Path(__file__).resolve().parent / ".tmp"
    root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(dir=root))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_bundled_obabel_binary_prefers_linux_bundle(monkeypatch) -> None:
    with workspace_tmp_dir() as tmp_path:
        linux_binary = tmp_path / "openbabel" / "bin" / "obabel"
        linux_binary.parent.mkdir(parents=True)
        linux_binary.write_text("", encoding="utf-8")
        monkeypatch.setattr(runtime, "runtime_root", lambda: tmp_path)

        assert runtime.bundled_obabel_binary() == str(linux_binary)


def test_bundled_obabel_binary_uses_vendor_fallback(monkeypatch) -> None:
    with workspace_tmp_dir() as tmp_path:
        vendor_binary = tmp_path / "vendor" / "openbabel" / "obabel.exe"
        vendor_binary.parent.mkdir(parents=True)
        vendor_binary.write_text("", encoding="utf-8")
        monkeypatch.setattr(runtime, "runtime_root", lambda: tmp_path)

        assert runtime.bundled_obabel_binary() == str(vendor_binary)


def test_bundled_mopac_binary_prefers_bundle(monkeypatch) -> None:
    with workspace_tmp_dir() as tmp_path:
        mopac_binary = tmp_path / "mopac" / "mopac.exe"
        mopac_binary.parent.mkdir(parents=True)
        mopac_binary.write_text("", encoding="utf-8")
        monkeypatch.setattr(runtime, "runtime_root", lambda: tmp_path)

        assert runtime.bundled_mopac_binary() == str(mopac_binary)


def test_openbabel_runtime_env_sets_linux_paths(monkeypatch) -> None:
    with workspace_tmp_dir() as tmp_path:
        openbabel_root = tmp_path / "openbabel"
        data_dir = openbabel_root / "data"
        plugins_dir = openbabel_root / "plugins"
        bin_dir = openbabel_root / "bin"
        lib_dir = openbabel_root / "lib"
        gui_dir = openbabel_root / "gui-data"

        for path in (data_dir, plugins_dir, bin_dir, lib_dir, gui_dir):
            path.mkdir(parents=True)

        monkeypatch.setattr(runtime, "runtime_root", lambda: tmp_path)
        env = runtime.openbabel_runtime_env({"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/usr/lib"})

        assert env["BABEL_DATADIR"] == str(data_dir)
        assert env["BABEL_LIBDIR"] == str(plugins_dir)
        assert env["BABEL_GUI"] == str(gui_dir)
        assert env["PATH"].startswith(f"{bin_dir};{lib_dir};") or env["PATH"].startswith(
            f"{bin_dir}:{lib_dir}:"
        )
        if os.name != "nt":
            assert env["LD_LIBRARY_PATH"].startswith(f"{lib_dir};{bin_dir};") or env[
                "LD_LIBRARY_PATH"
            ].startswith(f"{lib_dir}:{bin_dir}:")


def test_openbabel_runtime_env_sets_vendor_paths(monkeypatch) -> None:
    with workspace_tmp_dir() as tmp_path:
        openbabel_root = tmp_path / "vendor" / "openbabel"
        data_dir = openbabel_root / "data"
        plugins_dir = openbabel_root / "plugins"
        bin_dir = openbabel_root / "bin"
        lib_dir = openbabel_root / "lib"

        for path in (data_dir, plugins_dir, bin_dir, lib_dir):
            path.mkdir(parents=True)

        monkeypatch.setattr(runtime, "runtime_root", lambda: tmp_path)
        env = runtime.openbabel_runtime_env({"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/usr/lib"})

        assert env["BABEL_DATADIR"] == str(data_dir)
        assert env["BABEL_LIBDIR"] == str(plugins_dir)
        assert env["PATH"].startswith(f"{bin_dir};{lib_dir};") or env["PATH"].startswith(
            f"{bin_dir}:{lib_dir}:"
        )
