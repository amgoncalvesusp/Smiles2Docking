from __future__ import annotations

from src.utils.config import merge_settings, resolve_project_path, resolve_settings_paths


def test_output_dir_can_drive_report_and_log_locations() -> None:
    settings = {
        "input": {"file_path": "data/raw/sample_molecules.csv"},
        "export": {"output_dir": "custom_output", "temp_dir": "data/intermediate/tmp/export"},
        "reporting": {"report_dir": "data/reports", "use_output_dir": True},
        "logging": {"log_dir": "logs", "use_output_dir": True},
        "figures": {"output_dir": "data/reports/figures"},
        "protonation": {"temp_dir": "data/intermediate/tmp/protonation"},
        "pm7": {
            "temp_dir": "data/intermediate/tmp/mopac",
            "binary_path": "tools/mopac.exe",
            "preserved_files_dir": "custom_output/mopac_files",
        },
    }

    resolved = resolve_settings_paths(merge_settings(settings, {}))

    assert resolved["reporting"]["report_dir"] == resolve_project_path("custom_output")
    assert resolved["logging"]["log_dir"] == resolve_project_path("custom_output")
    assert resolved["pm7"]["temp_dir"] == resolve_project_path("data/intermediate/tmp/mopac")
    assert resolved["pm7"]["binary_path"] == resolve_project_path("tools/mopac.exe")
    assert resolved["pm7"]["preserved_files_dir"] == resolve_project_path("custom_output/mopac_files")
