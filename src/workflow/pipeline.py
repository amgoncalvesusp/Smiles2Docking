from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.database.spreadsheet_source import SpreadsheetSource, SpreadsheetSourceError
from src.export.mol2_writer import Mol2ExportError, StructureExporter
from src.preprocessing.smiles_cleaner import (
    AmbiguousFragmentError,
    InvalidSmilesError,
    SmilesCleaner,
)
from src.protonation.openbabel_adapter import OpenBabelError, OpenBabelProtonator
from src.quantum.mopac_adapter import MopacError, MopacOptimizer
from src.structure_generation.builder import StructureBuilder, StructureGenerationError
from src.utils.logging_utils import resolve_log_path
from src.utils.models import RunReport, WorkflowExecutionResult
from src.utils.reporting import write_report
from src.validation.structure_validator import StructureValidationError, StructureValidator


ProgressCallback = Callable[[int, int, str], None]
MessageCallback = Callable[[str], None]

PROGRESS_TEXT = {
    "en": {"processing": "Processing", "row": "row", "completed": "Completed"},
    "pt": {"processing": "Processando", "row": "linha", "completed": "Concluido"},
}


def run_workflow(
    settings: dict[str, Any],
    logger: logging.Logger,
    progress_callback: ProgressCallback | None = None,
    message_callback: MessageCallback | None = None,
) -> WorkflowExecutionResult:
    language = str(settings.get("ui", {}).get("language", "en")).lower()
    if language not in PROGRESS_TEXT:
        language = "en"
    report = RunReport(
        input_file=settings["input"]["file_path"],
        protonation_ph=float(settings["protonation"].get("ph", 7.4)),
        export_mode=str(settings["export"].get("mode", "separate_mol2")),
        pm7_enabled=bool(settings.get("pm7", {}).get("enabled", False)),
        pm7_method=str(settings.get("pm7", {}).get("method", "PM7")).upper()
        if settings.get("pm7", {}).get("enabled", False)
        else None,
        pm7_solvent_eps=float(settings.get("pm7", {}).get("eps", 78.39))
        if settings.get("pm7", {}).get("enabled", False) and settings.get("pm7", {}).get("use_eps", True)
        else None,
        pm7_files_preserved=bool(settings.get("pm7", {}).get("enabled", False) and settings.get("pm7", {}).get("preserve_files", False)),
        stereochemistry_policy=(
            "single_undefined_only"
            if settings.get("processing", {}).get("single_undefined_stereocenter_only", False)
            else "enumerate_all_with_cap"
            if settings.get("processing", {}).get("strict_stereochemistry", False)
            else "disabled"
        ),
    )
    if report.export_mode in {"single_sdf", "separate_sdf"}:
        report.export_format = "sdf"
    elif report.export_mode in {"single_pdbqt", "separate_pdbqt"}:
        report.export_format = "pdbqt"
    else:
        report.export_format = "mol2"
    report.log_file_path = str(resolve_log_path(settings))
    if report.pm7_files_preserved:
        report.pm7_preserved_files_dir = _resolve_pm7_preserved_files_dir(settings)
    batched_structures: list[tuple[str, Any]] = []

    def emit(level: int, message: str, *args: Any) -> None:
        logger.log(level, message, *args)
        if message_callback is not None:
            rendered = message % args if args else message
            message_callback(rendered)

    try:
        source = SpreadsheetSource(settings)
        cleaner = SmilesCleaner(settings["processing"])
        validator = StructureValidator(settings["processing"])
        report.stereochemistry_policy = validator.describe_stereochemistry_policy()
        protonator = OpenBabelProtonator(settings["protonation"])
        builder = StructureBuilder(settings["structure_generation"])
        pm7_settings = dict(settings.get("pm7", {}))
        if pm7_settings.get("enabled", False) and pm7_settings.get("preserve_files", False):
            pm7_settings["preserved_files_dir"] = _resolve_pm7_preserved_files_dir(settings)
        pm7_optimizer = MopacOptimizer(pm7_settings) if pm7_settings.get("enabled", False) else None
        exporter = StructureExporter(settings["export"], settings["protonation"])

        records = source.load_records()
        report.total_records_retrieved = len(records)
        total_records = len(records)

        for index, record in enumerate(records, start=1):
            if progress_callback is not None:
                target = record.access_code or f"{PROGRESS_TEXT[language]['row']} {record.source_row}"
                progress_callback(index - 1, total_records, f"{PROGRESS_TEXT[language]['processing']} {target}")

            if not record.access_code:
                report.failures_or_skipped_entries += 1
                report.failure_details.append(
                    {"access_code": "", "row": record.source_row, "reason": "Missing access code."}
                )
                emit(logging.WARNING, "Skipping row %s because access code is missing.", record.source_row)
                continue

            try:
                cleaned = cleaner.clean_record(record)
                report.molecules_successfully_cleaned += 1
                if cleaned.salts_removed:
                    report.molecules_with_salts_removed += 1

                undefined_stereo_analysis = validator.analyze_undefined_stereochemistry(
                    cleaned.cleaned_smiles,
                    record.access_code,
                )
                if undefined_stereo_analysis.should_skip:
                    skip_message = f"Skipped: undefined stereochemistry — {cleaned.cleaned_smiles}"
                    report.failures_or_skipped_entries += 1
                    report.records_with_undefined_stereochemistry += 1
                    report.stereochemistry_records_skipped += 1
                    report.stereochemistry_issues.append(
                        {
                            "access_code": record.access_code,
                            "row": record.source_row,
                            "undefined_centers": undefined_stereo_analysis.undefined_center_count,
                            "action": "skipped_undefined_stereo_filter",
                            "variant_count": 0,
                            "reason": skip_message,
                        }
                    )
                    report.failure_details.append(
                        {"access_code": record.access_code, "row": record.source_row, "reason": skip_message}
                    )
                    emit(logging.WARNING, skip_message)
                    continue

                validated_input_smiles = validator.validate_input_smiles(cleaned.cleaned_smiles, record.access_code)
                stereochemistry_resolution = validator.resolve_input_variants(validated_input_smiles, record.access_code)
                _register_stereochemistry_resolution(report, stereochemistry_resolution, record)
                variants = stereochemistry_resolution.variants
                if not variants:
                    report.failures_or_skipped_entries += 1
                    report.failure_details.append(
                        {
                            "access_code": record.access_code,
                            "row": record.source_row,
                            "reason": stereochemistry_resolution.reason or "Undefined stereochemistry policy rejected the record.",
                        }
                    )
                    emit(
                        logging.WARNING,
                        "Skipping %s because of unresolved stereochemistry: %s",
                        record.access_code,
                        stereochemistry_resolution.reason or "Undefined stereochemistry policy rejected the record.",
                    )
                    continue
                report.total_smiles_evaluated += len(variants)

                for variant in variants:
                    try:
                        protonated_smiles = protonator.protonate_smiles(variant.smiles, variant.access_code)
                        protonated_smiles = validator.validate_protonated_smiles(protonated_smiles, variant.access_code)
                        expected_charge = validator.formal_charge_from_smiles(protonated_smiles, variant.access_code)
                        molecule_3d = builder.build_3d(protonated_smiles, variant.access_code)
                        report.molecules_converted_to_3d += 1
                        if pm7_optimizer is not None:
                            pm7_result = pm7_optimizer.optimize(molecule_3d, variant.access_code)
                            molecule_3d = validator.validate_final_molecule(
                                pm7_result.molecule,
                                variant.access_code,
                                stage="post_pm7",
                                expected_charge=pm7_result.charge,
                            )
                            report.molecules_optimized_with_pm7 += 1
                            if pm7_result.preserved_files:
                                report.pm7_preserved_file_count += len(pm7_result.preserved_files)
                                report.pm7_preserved_files.extend(pm7_result.preserved_files)
                        else:
                            molecule_3d = validator.validate_final_molecule(
                                molecule_3d,
                                variant.access_code,
                                stage="pre_export",
                                expected_charge=expected_charge,
                            )

                        if exporter.uses_batch_export:
                            batched_structures.append((variant.access_code, molecule_3d))
                        else:
                            exported_paths = exporter.write(molecule_3d, variant.access_code)
                            _register_exported_paths(report, exported_paths, exporter.export_format)
                            report.structure_records_exported += 1
                        emit(
                            logging.INFO,
                            "Processed %s with force field %s%s%s",
                            variant.access_code,
                            molecule_3d.GetProp("force_field") if molecule_3d.HasProp("force_field") else "unknown",
                            f" and {molecule_3d.GetProp('mopac_method')}" if molecule_3d.HasProp("mopac_method") else "",
                            (
                                f" using validation rescue {molecule_3d.GetProp('validation_rescue')}"
                                if molecule_3d.HasProp("validation_rescue")
                                else ""
                            ),
                        )
                    except (
                        OpenBabelError,
                        StructureGenerationError,
                        StructureValidationError,
                        Mol2ExportError,
                        SpreadsheetSourceError,
                        MopacError,
                    ) as exc:
                        report.failures_or_skipped_entries += 1
                        report.failure_details.append(
                            {"access_code": variant.access_code, "row": record.source_row, "reason": str(exc)}
                        )
                        emit(logging.ERROR, "Processing failed for %s: %s", variant.access_code, exc)
                        continue
            except InvalidSmilesError as exc:
                report.invalid_smiles += 1
                report.failures_or_skipped_entries += 1
                report.failure_details.append(
                    {"access_code": record.access_code, "row": record.source_row, "reason": str(exc)}
                )
                emit(logging.WARNING, "Skipping invalid SMILES for %s: %s", record.access_code, exc)
            except (StructureValidationError, SpreadsheetSourceError) as exc:
                report.failures_or_skipped_entries += 1
                report.failure_details.append(
                    {"access_code": record.access_code, "row": record.source_row, "reason": str(exc)}
                )
                emit(logging.ERROR, "Processing failed for %s: %s", record.access_code, exc)
            except AmbiguousFragmentError as exc:
                report.failures_or_skipped_entries += 1
                report.status = "aborted_for_clarification"
                report.abort_reason = str(exc)
                report.failure_details.append(
                    {"access_code": record.access_code, "row": record.source_row, "reason": str(exc)}
                )
                emit(logging.ERROR, "Execution stopped: %s", exc)
                raise
            finally:
                if progress_callback is not None:
                    target = record.access_code or f"{PROGRESS_TEXT[language]['row']} {record.source_row}"
                    progress_callback(index, total_records, f"{PROGRESS_TEXT[language]['completed']} {target}")

        if batched_structures:
            exported_paths = exporter.write_batch(batched_structures)
            _register_exported_paths(report, exported_paths, exporter.export_format)
            report.structure_records_exported += len(batched_structures)
            emit(
                logging.INFO,
                "Merged %s molecules into %s",
                len(batched_structures),
                ", ".join(str(path) for path in exported_paths),
            )
    except SpreadsheetSourceError as exc:
        report.status = "failed"
        report.abort_reason = str(exc)
        emit(logging.ERROR, "Input loading failed: %s", exc)
        report_path = write_report(report, settings["reporting"]["report_dir"])
        emit(logging.INFO, "Run report written to %s", report_path)
        return WorkflowExecutionResult(report=report, report_path=str(report_path))
    except AmbiguousFragmentError:
        report_path = write_report(report, settings["reporting"]["report_dir"])
        emit(logging.INFO, "Run report written to %s", report_path)
        return WorkflowExecutionResult(report=report, report_path=str(report_path))

    report_path = write_report(report, settings["reporting"]["report_dir"])
    emit(logging.INFO, "Run report written to %s", report_path)
    return WorkflowExecutionResult(report=report, report_path=str(report_path))


def _register_exported_paths(report: RunReport, exported_paths: list[Any], export_format: str) -> None:
    report.structure_files_written += len(exported_paths)
    report.generated_structure_files.extend(str(path) for path in exported_paths)
    if export_format == "mol2":
        report.mol2_files_written += len(exported_paths)
        report.generated_mol2_files.extend(str(path) for path in exported_paths)
    elif export_format == "pdbqt":
        report.pdbqt_files_written += len(exported_paths)
        report.generated_pdbqt_files.extend(str(path) for path in exported_paths)


def _register_stereochemistry_resolution(report: RunReport, resolution: Any, record: Any) -> None:
    if getattr(resolution, "undefined_center_count", 0) <= 0:
        return

    report.records_with_undefined_stereochemistry += 1
    if getattr(resolution, "variants", []):
        report.stereochemistry_records_enumerated += 1
    else:
        report.stereochemistry_records_skipped += 1

    report.stereochemistry_issues.append(
        {
            "access_code": record.access_code,
            "row": record.source_row,
            "undefined_centers": resolution.undefined_center_count,
            "action": resolution.action,
            "variant_count": len(resolution.variants),
            "reason": resolution.reason or "",
        }
    )


def _resolve_pm7_preserved_files_dir(settings: dict[str, Any]) -> str:
    configured = str(settings.get("pm7", {}).get("preserved_files_dir", "")).strip()
    if configured:
        return configured
    return str(Path(settings["export"]["output_dir"]) / "mopac_files")
