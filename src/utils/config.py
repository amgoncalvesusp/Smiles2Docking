from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"


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
    for section, key in path_settings:
        value = settings.get(section, {}).get(key)
        if value:
            settings[section][key] = resolve_project_path(value)
    export_output_dir = settings.get("export", {}).get("output_dir")
    if export_output_dir:
        if settings.get("reporting", {}).get("use_output_dir", False):
            settings.setdefault("reporting", {})["report_dir"] = export_output_dir
        if settings.get("logging", {}).get("use_output_dir", False):
            settings.setdefault("logging", {})["log_dir"] = export_output_dir
    return settings
