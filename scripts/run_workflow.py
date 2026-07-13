from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import torch before RDKit to keep the Windows DLL load order deterministic.
import src.utils.torch_preimport  # noqa: F401,E402

from src.utils.config import (
    load_settings,
    merge_settings,
    resolve_project_path,
    resolve_settings_paths,
)
from src.utils.logging_utils import setup_logging
from src.workflow.pipeline import run_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare molecules from spreadsheet/Excel input."
    )
    parser.add_argument(
        "--config", default=str(PROJECT_ROOT / "config" / "settings.yaml")
    )
    parser.add_argument("--input", help="Path to CSV/XLS/XLSX file.")
    parser.add_argument("--sheet", help="Excel sheet name.")
    parser.add_argument("--smiles-column", help="Column containing SMILES.")
    parser.add_argument("--access-code-column", help="Column containing access codes.")
    parser.add_argument("--ph", type=float, help="Target pH for protonation.")
    parser.add_argument(
        "--export-mode",
        choices=("separate_mol2", "separate_sdf", "single_mol2", "single_sdf"),
        help="Choose whether to export separate MOL2/SDF files or a single MOL2/SDF bundle.",
    )
    parser.add_argument(
        "--output-name",
        "--bundle-name",
        dest="bundle_name",
        help="Base filename for single-file exports or optional prefix for separate-file exports.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for exported structures, report and workflow log.",
    )
    return parser.parse_args()


def build_overrides(args: argparse.Namespace) -> dict:
    input_overrides: dict[str, str] = {}
    if args.input:
        input_overrides["file_path"] = resolve_project_path(args.input)
    if args.sheet:
        input_overrides["sheet_name"] = args.sheet
    if args.smiles_column:
        input_overrides["smiles_column"] = args.smiles_column
    if args.access_code_column:
        input_overrides["access_code_column"] = args.access_code_column
    overrides: dict[str, dict] = {"input": input_overrides}
    export_overrides: dict[str, str] = {}
    if args.export_mode:
        export_overrides["mode"] = args.export_mode
    if args.bundle_name:
        export_overrides["bundle_basename"] = args.bundle_name
    if args.output_dir:
        export_overrides["output_dir"] = resolve_project_path(args.output_dir)
    if export_overrides:
        overrides["export"] = export_overrides
    if args.ph is not None:
        overrides["protonation"] = {"ph": args.ph}
    return overrides


def main() -> int:
    args = parse_args()
    settings = merge_settings(load_settings(args.config), build_overrides(args))

    if not settings["input"].get("file_path"):
        raise SystemExit(
            "An input spreadsheet file is required. Use --input or set input.file_path in config/settings.yaml."
        )

    settings = resolve_settings_paths(settings)

    logger = setup_logging(settings)
    result = run_workflow(settings, logger=logger)
    if result.report.status == "failed":
        return 1
    if result.report.status == "aborted_for_clarification":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
