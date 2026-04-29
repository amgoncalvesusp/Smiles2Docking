from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.quantum.mopac_methods import normalize_mopac_method
from src.utils.config import load_settings, merge_settings, resolve_project_path, resolve_settings_paths
from src.utils.logging_utils import setup_logging
from src.workflow.pipeline import run_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare molecules from spreadsheet/Excel input.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "settings.yaml"))
    parser.add_argument("--input", help="Path to CSV/XLS/XLSX file.")
    parser.add_argument("--sheet", help="Excel sheet name.")
    parser.add_argument("--smiles-column", help="Column containing SMILES.")
    parser.add_argument("--access-code-column", help="Column containing access codes.")
    parser.add_argument("--ph", type=float, help="Target pH for protonation.")
    parser.add_argument(
        "--skip-undefined-stereo",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Skip molecules with undefined stereochemistry before protonation. "
            "This also evaluates tertiary amine nitrogens that would become asymmetric upon protonation."
        ),
    )
    parser.add_argument(
        "--strict-stereochemistry",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enumerate unresolved tetrahedral stereochemistry before protonation and export each variant separately.",
    )
    parser.add_argument(
        "--single-undefined-stereocenter-only",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Only enumerate molecules when exactly one tetrahedral stereocenter is undefined. Molecules with two or more undefined centers are reported and skipped.",
    )
    parser.add_argument(
        "--max-stereochemistry-variants",
        type=int,
        help="Maximum number of stereochemistry variants to enumerate for one record before skipping it.",
    )
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
    parser.add_argument("--output-dir", help="Directory for exported structures, report and workflow log.")
    parser.add_argument(
        "--pm7",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable the MOPAC PM7 optimization stage.",
    )
    parser.add_argument(
        "--mopac-method",
        "--pm7-method",
        dest="mopac_method",
        help="MOPAC method keyword. Defaults to PM7, but accepts other valid MOPAC methods such as PM6, PM6-D3H4X, PM3, AM1, RM1, or MNDO.",
    )
    parser.add_argument(
        "--pm7-solvent",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable COSMO solvent treatment with EPS during PM7 calculations.",
    )
    parser.add_argument("--pm7-eps", type=float, help="Dielectric constant used when PM7 solvent is enabled.")
    parser.add_argument(
        "--preserve-mopac-files",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Preserve the generated MOPAC job files in a results subfolder.",
    )
    parser.add_argument(
        "--pm7-charge-rescue",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable constrained post-PM7 charge rescue for invalid structures.",
    )
    parser.add_argument("--mopac-files-dir", help="Optional directory where preserved MOPAC files should be copied.")
    parser.add_argument("--mopac-binary", help="Optional path to the MOPAC executable.")
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
    processing_overrides: dict[str, object] = {}
    if args.skip_undefined_stereo is not None:
        processing_overrides["skip_undefined_stereo"] = args.skip_undefined_stereo
    if args.strict_stereochemistry is not None:
        processing_overrides["strict_stereochemistry"] = args.strict_stereochemistry
    if args.single_undefined_stereocenter_only is not None:
        processing_overrides["single_undefined_stereocenter_only"] = args.single_undefined_stereocenter_only
    if args.max_stereochemistry_variants is not None:
        processing_overrides["max_stereochemistry_variants"] = args.max_stereochemistry_variants
    if args.pm7_charge_rescue is not None:
        processing_overrides["allow_post_mopac_charge_rescue"] = args.pm7_charge_rescue
    if processing_overrides:
        overrides["processing"] = processing_overrides
    pm7_overrides: dict[str, object] = {}
    if args.pm7 is not None:
        pm7_overrides["enabled"] = args.pm7
    if args.mopac_method:
        pm7_overrides["method"] = normalize_mopac_method(args.mopac_method)
    if args.pm7_solvent is not None:
        pm7_overrides["use_eps"] = args.pm7_solvent
    if args.pm7_eps is not None:
        pm7_overrides["eps"] = args.pm7_eps
    if args.preserve_mopac_files is not None:
        pm7_overrides["preserve_files"] = args.preserve_mopac_files
    if args.mopac_files_dir:
        pm7_overrides["preserved_files_dir"] = resolve_project_path(args.mopac_files_dir)
    if args.mopac_binary:
        pm7_overrides["binary_path"] = resolve_project_path(args.mopac_binary)
    if pm7_overrides:
        overrides["pm7"] = pm7_overrides
    return overrides


def main() -> int:
    args = parse_args()
    settings = merge_settings(load_settings(args.config), build_overrides(args))

    if not settings["input"].get("file_path"):
        raise SystemExit("An input spreadsheet file is required. Use --input or set input.file_path in config/settings.yaml.")

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
