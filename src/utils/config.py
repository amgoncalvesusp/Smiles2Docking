from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from src.utils.app_paths import is_appimage, is_frozen, user_cache_dir, user_data_dir, user_log_dir


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"

# Writable path keys redirected to per-user directories on read-only installs
# (PyInstaller frozen builds, Linux AppImage). Keyed by (section, key) -> kind.
_WRITABLE_PATH_REDIRECTS = {
    ("export", "output_dir"): "processed",
    ("export", "temp_dir"): "export_tmp",
    ("reporting", "report_dir"): "reports",
    ("figures", "output_dir"): "figures",
    ("logging", "log_dir"): "logs",
    ("protonation", "temp_dir"): "protonation_tmp",
    ("pm7", "temp_dir"): "mopac_tmp",
    ("pm7", "preserved_files_dir"): "mopac_files",
}


def _install_is_read_only() -> bool:
    return is_frozen() or is_appimage()


def _user_base_for(kind: str) -> Path:
    if kind == "logs":
        return user_log_dir()
    if kind in {"export_tmp", "protonation_tmp", "mopac_tmp"}:
        return user_cache_dir() / "intermediate" / kind.replace("_tmp", "")
    return user_data_dir() / kind


def load_settings(config_path: str | None = None) -> dict[str, Any]:
    target = Path(config_path) if config_path else DEFAULT_SETTINGS_PATH
    with target.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def merge_settings(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_project_path(path_value: str) -> str:
    path = Path(path_value)
    return str(path if path.is_absolute() else PROJECT_ROOT / path)


def resolve_settings_paths(settings: dict[str, Any]) -> dict[str, Any]:
    path_settings = (
        ("input", "file_path"),
        ("export", "output_dir"),
        ("export", "temp_dir"),
        ("reporting", "report_dir"),
        ("figures", "output_dir"),
        ("logging", "log_dir"),
        ("protonation", "temp_dir"),
        ("pm7", "temp_dir"),
        ("pm7", "binary_path"),
        ("pm7", "preserved_files_dir"),
    )
    read_only_install = _install_is_read_only()
    for section, key in path_settings:
        value = settings.get(section, {}).get(key)
        if not value:
            continue
        redirect_kind = _WRITABLE_PATH_REDIRECTS.get((section, key))
        if read_only_install and redirect_kind is not None and not Path(value).is_absolute():
            settings[section][key] = str(_user_base_for(redirect_kind))
        else:
            settings[section][key] = resolve_project_path(value)
    export_output_dir = settings.get("export", {}).get("output_dir")
    if export_output_dir:
        if settings.get("reporting", {}).get("use_output_dir", False):
            settings.setdefault("reporting", {})["report_dir"] = export_output_dir
        if settings.get("logging", {}).get("use_output_dir", False):
            settings.setdefault("logging", {})["log_dir"] = export_output_dir
    return settings
