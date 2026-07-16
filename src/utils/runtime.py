from __future__ import annotations

import os
import sys
from pathlib import Path

from src.utils.config import PROJECT_ROOT


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return PROJECT_ROOT


def resolve_runtime_path(*parts: str) -> Path:
    return runtime_root().joinpath(*parts)


def get_mopac_executable_path() -> str:
    return str(resolve_runtime_path("vendor", "mopac", "MOPAC.exe"))


def _first_existing_path(*candidates: Path) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _prepend_env_path(env: dict[str, str], key: str, *paths: Path) -> None:
    existing = env.get(key, "")
    ordered_paths = [str(path) for path in paths if path.exists()]
    if not ordered_paths:
        return
    if existing:
        env[key] = os.pathsep.join([*ordered_paths, existing])
    else:
        env[key] = os.pathsep.join(ordered_paths)


def bundled_obabel_binary(default_binary: str = "obabel") -> str:
    candidates = (
        resolve_runtime_path("openbabel", "obabel.exe"),
        resolve_runtime_path("openbabel", "obabel"),
        resolve_runtime_path("openbabel", "bin", "obabel"),
        resolve_runtime_path("vendor", "openbabel", "obabel.exe"),
        resolve_runtime_path("vendor", "openbabel", "obabel"),
        resolve_runtime_path("vendor", "openbabel", "bin", "obabel"),
        resolve_runtime_path("Library", "bin", "obabel.exe"),
    )
    candidate = _first_existing_path(*candidates)
    if candidate is not None:
        return str(candidate)
    return default_binary


def bundled_mopac_binary(
    configured_path: str | None = None, default_binary: str = "mopac"
) -> str:
    del default_binary
    candidates: list[Path] = [
        resolve_runtime_path("mopac", "mopac.exe"),
        resolve_runtime_path("mopac", "MOPAC.exe"),
        resolve_runtime_path("mopac", "bin", "mopac"),
        resolve_runtime_path("mopac", "bin", "mopac.exe"),
        Path(get_mopac_executable_path()),
        # Linux/macOS: MOPAC is bundled under vendor/mopac/bin (frozen build) or
        # vendor/mopac-linux/bin (source tree); its RUNPATH ($ORIGIN/../lib) finds
        # the bundled libmopac/libiomp5.
        resolve_runtime_path("vendor", "mopac", "bin", "mopac"),
        resolve_runtime_path("vendor", "mopac-linux", "bin", "mopac"),
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "MOPAC"
        / "bin"
        / "MOPAC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "MOPAC"
        / "bin"
        / "mopac.exe",
    ]
    if configured_path:
        candidates.insert(0, Path(configured_path))

    candidate = _first_existing_path(*candidates)
    if candidate is not None:
        _ensure_executable(candidate)
        return str(candidate)
    return str(candidates[0])


def _ensure_executable(path: Path) -> None:
    """Add the user execute bit on POSIX (PyInstaller data files lose it)."""
    if os.name == "nt":
        return
    try:
        mode = path.stat().st_mode
        if not mode & 0o100:
            path.chmod(mode | 0o111)
    except OSError:
        pass


def openbabel_runtime_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    openbabel_root = _first_existing_path(
        resolve_runtime_path("openbabel"),
        resolve_runtime_path("vendor", "openbabel"),
    ) or resolve_runtime_path("openbabel")
    openbabel_data_dir = openbabel_root / "data"
    openbabel_gui_data_dir = openbabel_root / "gui-data"
    openbabel_bin_dir = openbabel_root
    openbabel_plugins_dir = _first_existing_path(
        openbabel_root / "plugins",
        openbabel_root,
    )
    openbabel_runtime_bin_dir = _first_existing_path(
        openbabel_root / "bin",
        openbabel_bin_dir,
    )
    openbabel_library_dir = _first_existing_path(
        openbabel_root / "lib",
        openbabel_bin_dir,
    )
    if openbabel_data_dir.exists():
        env["BABEL_DATADIR"] = str(openbabel_data_dir)
    if openbabel_plugins_dir is not None:
        env["BABEL_LIBDIR"] = str(openbabel_plugins_dir)
    _prepend_env_path(
        env,
        "PATH",
        *(path for path in (openbabel_runtime_bin_dir, openbabel_library_dir) if path),
    )
    if os.name != "nt":
        _prepend_env_path(
            env,
            "LD_LIBRARY_PATH",
            *(
                path
                for path in (openbabel_library_dir, openbabel_runtime_bin_dir)
                if path
            ),
        )
    if openbabel_gui_data_dir.exists():
        env["BABEL_GUI"] = str(openbabel_gui_data_dir)
    return env
