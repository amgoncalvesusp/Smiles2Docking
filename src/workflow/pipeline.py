from __future__ import annotations

import logging
import os
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rdkit import Chem

from src.database.spreadsheet_source import SpreadsheetSource, SpreadsheetSourceError
from src.export.mol2_writer import Mol2ExportError, StructureExporter
from src.preprocessing.smiles_cleaner import (
    AmbiguousFragmentError,
    InvalidSmilesError,
    SmilesCleaner,
)
from src.protonation.base import ProtonationError, iter_protonation_states
from src.protonation.charge_normalization import normalize_anion_placement
from src.protonation.factory import build_protonator
from src.protonation.openbabel_adapter import OpenBabelError
from src.quantum.mopac_adapter import MopacError, MopacOptimizer
from src.structure_generation.builder import StructureBuilder, StructureGenerationError
from src.tautomer.base import TautomerError
from src.tautomer.factory import build_tautomerizer
from src.utils.logging_utils import resolve_log_path
from src.utils.models import RunReport, WorkflowExecutionResult
from src.utils.reporting import write_report
from src.validation.structure_validator import (
    StructureValidationError,
    StructureValidator,
)


ProgressCallback = Callable[[int, int, str], None]
MessageCallback = Callable[[str], None]

PROGRESS_TEXT = {
    "en": {"processing": "Processing", "row": "row", "completed": "Completed"},
    "pt": {"processing": "Processando", "row": "linha", "completed": "Concluido"},
}

# Per-variant errors that downgrade a single variant to a logged failure
# instead of aborting the record or the run.
VARIANT_ERRORS = (
    OpenBabelError,
    ProtonationError,
    TautomerError,
    StructureGenerationError,
    StructureValidationError,
    Mol2ExportError,
    SpreadsheetSourceError,
    MopacError,
)


@dataclass(slots=True)
class _VariantResult:
    """Picklable outcome of preparing a single stereochemistry variant."""

    access_code: str
    seconds: float = 0.0
    molecule: Any | None = None
    pm7_used: bool = False
    preserved_files: list[str] = field(default_factory=list)
    force_field: str | None = None
    mopac_method: str | None = None
    validation_rescue: str | None = None
    error: str | None = None


@dataclass(slots=True)
class _RecordOutcome:
    """All report deltas produced by preparing one input record.

    Built in a worker process (parallel) or inline (sequential) and then
    replayed against the shared RunReport in the main thread by
    ``_apply_outcome``. Holds no live handles so it survives pickling.
    """

    source_row: int
    access_code: str
    missing_access_code: bool = False
    cleaned: bool = False
    salts_removed: bool = False
    undefined_skip_message: str | None = None
    undefined_center_count: int = 0
    stereo_issue: dict[str, Any] | None = None
    stereo_enumerated: bool = False
    stereo_skipped: bool = False
    stereo_undefined_record: bool = False
    invalid_smiles: bool = False
    record_error: str | None = None
    ambiguous_error: str | None = None
    no_variants_reason: str | None = None
    variant_count: int = 0
    protonation_states_generated: int = 0
    variants: list[_VariantResult] = field(default_factory=list)


@dataclass(slots=True)
class _Components:
    cleaner: SmilesCleaner
    validator: StructureValidator
    protonator: Any
    builder: StructureBuilder
    pm7_optimizer: MopacOptimizer | None
    tautomerizer: Any = None


def _build_components(settings: dict[str, Any]) -> _Components:
    pm7_settings = dict(settings.get("pm7", {}))
    if pm7_settings.get("enabled", False) and pm7_settings.get("preserve_files", False):
        pm7_settings["preserved_files_dir"] = _resolve_pm7_preserved_files_dir(settings)
    pm7_optimizer = (
        MopacOptimizer(pm7_settings) if pm7_settings.get("enabled", False) else None
    )
    # The tautomer step may protonate at the target pH (sPhysNet-Taut), so it is
    # given the same pH as the protonation stage.
    tautomer_settings = dict(settings.get("tautomer") or {})
    if "ph" not in tautomer_settings:
        tautomer_settings["ph"] = settings.get("protonation", {}).get("ph", 7.4)
    return _Components(
        cleaner=SmilesCleaner(settings["processing"]),
        validator=StructureValidator(settings["processing"]),
        protonator=build_protonator(settings["protonation"]),
        builder=StructureBuilder(settings["structure_generation"]),
        pm7_optimizer=pm7_optimizer,
        tautomerizer=build_tautomerizer(tautomer_settings),
    )


def _resolve_n_jobs(settings: dict[str, Any]) -> int:
    """Effective worker count. Returns 1 (sequential) unless parallel enabled."""
    parallel = settings.get("parallel", {})
    if not isinstance(parallel, dict) or not parallel.get("enabled", False):
        return 1
    try:
        requested = int(parallel.get("n_jobs", -1))
    except (TypeError, ValueError):
        return 1
    if requested == 0:
        return 1
    if requested < 0:
        return max(1, os.cpu_count() or 1)
    return requested


def _prepare_record(record: Any, components: _Components) -> _RecordOutcome:
    """Pure record preparation: clean, validate, protonate, build 3D, PM7.

    Performs no logging and no file IO so it is safe to run in a worker
    process. Export and report mutation happen in the main thread via
    ``_apply_outcome``.
    """
    outcome = _RecordOutcome(
        source_row=record.source_row, access_code=record.access_code
    )

    if not record.access_code:
        outcome.missing_access_code = True
        return outcome

    cleaner = components.cleaner
    validator = components.validator
    protonator = components.protonator
    builder = components.builder
    pm7_optimizer = components.pm7_optimizer
    tautomerizer = components.tautomerizer

    try:
        cleaned = cleaner.clean_record(record)
        outcome.cleaned = True
        outcome.salts_removed = bool(cleaned.salts_removed)

        undefined_stereo_analysis = validator.analyze_undefined_stereochemistry(
            cleaned.cleaned_smiles, record.access_code
        )
        if undefined_stereo_analysis.should_skip:
            skip_message = (
                f"Skipped: undefined stereochemistry — {cleaned.cleaned_smiles}"
            )
            outcome.undefined_skip_message = skip_message
            outcome.undefined_center_count = (
                undefined_stereo_analysis.undefined_center_count
            )
            return outcome

        validated_input_smiles = validator.validate_input_smiles(
            cleaned.cleaned_smiles, record.access_code
        )
        stereochemistry_resolution = validator.resolve_input_variants(
            validated_input_smiles, record.access_code
        )
        _capture_stereochemistry_resolution(outcome, stereochemistry_resolution, record)
        variants = stereochemistry_resolution.variants
        if not variants:
            outcome.no_variants_reason = (
                stereochemistry_resolution.reason
                or "Undefined stereochemistry policy rejected the record."
            )
            return outcome

        # Fan each stereochemistry variant out over its protonation states.
        # Single-state backends (MolGpKa, Open Babel, none) yield exactly one
        # state and keep the original access code, so their output is identical
        # to the pre-1.3 pipeline. Enumeration backends (Dimorphite-DL) yield
        # several states, each exported under a suffixed access code.
        prepared: list[_VariantResult] = []
        states_total = 0
        for variant in variants:
            try:
                variant_smiles = variant.smiles
                already_protonated = False
                if tautomerizer is not None:
                    variant_smiles = tautomerizer.dominant_tautomer(
                        variant_smiles, variant.access_code
                    )
                    # sPhysNet-Taut protonates at the requested pH as part of the
                    # tautomer step; its output must not be protonated again.
                    already_protonated = getattr(
                        tautomerizer, "produces_protonated", False
                    )
                if already_protonated:
                    states = [variant_smiles]
                else:
                    states = iter_protonation_states(
                        protonator, variant_smiles, variant.access_code
                    )
            except VARIANT_ERRORS as exc:
                prepared.append(
                    _VariantResult(access_code=variant.access_code, error=str(exc))
                )
                continue
            states_total += len(states)
            multi = len(states) > 1
            for index, protonated_smiles in enumerate(states, start=1):
                code = (
                    f"{variant.access_code}_p{index}" if multi else variant.access_code
                )
                prepared.append(
                    _prepare_variant(code, protonated_smiles, components, pm7_optimizer)
                )
        outcome.variants = prepared
        outcome.variant_count = len(prepared)
        outcome.protonation_states_generated = states_total
    except InvalidSmilesError as exc:
        outcome.invalid_smiles = True
        outcome.record_error = str(exc)
    except AmbiguousFragmentError as exc:
        outcome.ambiguous_error = str(exc)
    except (StructureValidationError, SpreadsheetSourceError) as exc:
        outcome.record_error = str(exc)

    return outcome


def _prepare_variant(
    access_code: str,
    protonated_smiles: str,
    components: _Components,
    pm7_optimizer: MopacOptimizer | None,
) -> _VariantResult:
    """Build and validate one already-protonated variant/state.

    Protonation happens upstream in :func:`_prepare_record` so a single SMILES
    can fan out into several states; this function receives the protonated
    SMILES directly.
    """
    validator = components.validator
    builder = components.builder
    result = _VariantResult(access_code=access_code)
    variant_start = time.perf_counter()
    try:
        protonated_smiles = validator.validate_protonated_smiles(
            protonated_smiles, access_code
        )
        # Move any carbon-centred anion onto an adjacent heteroatom (e.g. a
        # 1,3-diketone carbanion to its enolate) so the formal charge survives
        # export to MOL2, whose SYBYL atom types cannot encode a charge on carbon.
        protonated_smiles = normalize_anion_placement(protonated_smiles)
        expected_charge = validator.formal_charge_from_smiles(
            protonated_smiles, access_code
        )
        molecule_3d = builder.build_3d(protonated_smiles, access_code)
        if pm7_optimizer is not None:
            pm7_result = pm7_optimizer.optimize(molecule_3d, access_code)
            molecule_3d = validator.validate_final_molecule(
                pm7_result.molecule,
                access_code,
                stage="post_pm7",
                expected_charge=pm7_result.charge,
            )
            result.pm7_used = True
            result.preserved_files = list(pm7_result.preserved_files)
        else:
            molecule_3d = validator.validate_final_molecule(
                molecule_3d,
                access_code,
                stage="pre_export",
                expected_charge=expected_charge,
            )
        result.molecule = molecule_3d
        if molecule_3d.HasProp("force_field"):
            result.force_field = molecule_3d.GetProp("force_field")
        if molecule_3d.HasProp("mopac_method"):
            result.mopac_method = molecule_3d.GetProp("mopac_method")
        if molecule_3d.HasProp("validation_rescue"):
            result.validation_rescue = molecule_3d.GetProp("validation_rescue")
    except VARIANT_ERRORS as exc:
        result.error = str(exc)
    result.seconds = round(time.perf_counter() - variant_start, 4)
    return result


def _prepare_record_worker(settings: dict[str, Any], record: Any) -> _RecordOutcome:
    """Top-level entry point for joblib workers (must be picklable)."""
    Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
    components = _build_components(settings)
    return _prepare_record(record, components)


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
        if settings.get("pm7", {}).get("enabled", False)
        and settings.get("pm7", {}).get("use_eps", True)
        else None,
        pm7_files_preserved=bool(
            settings.get("pm7", {}).get("enabled", False)
            and settings.get("pm7", {}).get("preserve_files", False)
        ),
        stereochemistry_policy=(
            "single_undefined_only"
            if settings.get("processing", {}).get(
                "single_undefined_stereocenter_only", False
            )
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
    report.started_at = datetime.now(timezone.utc).isoformat()
    wall_clock_start = time.perf_counter()

    def emit(level: int, message: str, *args: Any) -> None:
        logger.log(level, message, *args)
        if message_callback is not None:
            rendered = message % args if args else message
            message_callback(rendered)

    n_jobs = _resolve_n_jobs(settings)
    report.n_jobs_used = n_jobs

    try:
        source = SpreadsheetSource(settings)
        components = _build_components(settings)
        report.stereochemistry_policy = (
            components.validator.describe_stereochemistry_policy()
        )
        report.protonation_backend = getattr(
            components.protonator, "backend_name", "openbabel"
        )
        exporter = StructureExporter(settings["export"], settings["protonation"])

        records = source.load_records()
        report.total_records_retrieved = len(records)
        total_records = len(records)

        if n_jobs > 1 and total_records > 1:
            Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
            outcomes = _run_records_parallel(settings, records, n_jobs)
        else:
            outcomes = (_prepare_record(record, components) for record in records)

        for index, (record, outcome) in enumerate(zip(records, outcomes), start=1):
            if progress_callback is not None:
                target = (
                    record.access_code
                    or f"{PROGRESS_TEXT[language]['row']} {record.source_row}"
                )
                progress_callback(
                    index - 1,
                    total_records,
                    f"{PROGRESS_TEXT[language]['processing']} {target}",
                )
            try:
                _apply_outcome(report, outcome, exporter, emit, batched_structures)
            finally:
                if progress_callback is not None:
                    target = (
                        record.access_code
                        or f"{PROGRESS_TEXT[language]['row']} {record.source_row}"
                    )
                    progress_callback(
                        index,
                        total_records,
                        f"{PROGRESS_TEXT[language]['completed']} {target}",
                    )

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
        _finalize_timing(report, wall_clock_start)
        report_path = _write_report(report, settings)
        report_path and emit(logging.INFO, "Run report written to %s", report_path)
        return WorkflowExecutionResult(report=report, report_path=str(report_path))
    except AmbiguousFragmentError:
        _finalize_timing(report, wall_clock_start)
        report_path = _write_report(report, settings)
        report_path and emit(logging.INFO, "Run report written to %s", report_path)
        return WorkflowExecutionResult(report=report, report_path=str(report_path))

    _finalize_timing(report, wall_clock_start)
    report_path = _write_report(report, settings)
    report_path and emit(logging.INFO, "Run report written to %s", report_path)
    return WorkflowExecutionResult(report=report, report_path=str(report_path))


def _run_records_parallel(
    settings: dict[str, Any], records: list[Any], n_jobs: int
) -> list[_RecordOutcome]:
    from joblib import Parallel, delayed

    parallel_settings = settings.get("parallel", {})
    backend = str(parallel_settings.get("backend", "loky"))
    batch_size = parallel_settings.get("batch_size", "auto")
    runner = Parallel(n_jobs=n_jobs, backend=backend, batch_size=batch_size)
    return list(
        runner(delayed(_prepare_record_worker)(settings, record) for record in records)
    )


def _apply_outcome(
    report: RunReport,
    outcome: _RecordOutcome,
    exporter: StructureExporter,
    emit: Callable[..., None],
    batched_structures: list[tuple[str, Any]],
) -> None:
    """Replay a prepared record's deltas against the shared report (main thread)."""
    if outcome.missing_access_code:
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {
                "access_code": "",
                "row": outcome.source_row,
                "reason": "Missing access code.",
            }
        )
        emit(
            logging.WARNING,
            "Skipping row %s because access code is missing.",
            outcome.source_row,
        )
        return

    if outcome.ambiguous_error is not None:
        report.failures_or_skipped_entries += 1
        report.status = "aborted_for_clarification"
        report.abort_reason = outcome.ambiguous_error
        report.failure_details.append(
            {
                "access_code": outcome.access_code,
                "row": outcome.source_row,
                "reason": outcome.ambiguous_error,
            }
        )
        emit(logging.ERROR, "Execution stopped: %s", outcome.ambiguous_error)
        raise AmbiguousFragmentError(outcome.ambiguous_error)

    if outcome.invalid_smiles:
        report.invalid_smiles += 1
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {
                "access_code": outcome.access_code,
                "row": outcome.source_row,
                "reason": outcome.record_error or "",
            }
        )
        emit(
            logging.WARNING,
            "Skipping invalid SMILES for %s: %s",
            outcome.access_code,
            outcome.record_error,
        )
        return

    if outcome.cleaned:
        report.molecules_successfully_cleaned += 1
        if outcome.salts_removed:
            report.molecules_with_salts_removed += 1

    if outcome.undefined_skip_message is not None:
        report.failures_or_skipped_entries += 1
        report.records_with_undefined_stereochemistry += 1
        report.stereochemistry_records_skipped += 1
        report.stereochemistry_issues.append(
            {
                "access_code": outcome.access_code,
                "row": outcome.source_row,
                "undefined_centers": outcome.undefined_center_count,
                "action": "skipped_undefined_stereo_filter",
                "variant_count": 0,
                "reason": outcome.undefined_skip_message,
            }
        )
        report.failure_details.append(
            {
                "access_code": outcome.access_code,
                "row": outcome.source_row,
                "reason": outcome.undefined_skip_message,
            }
        )
        emit(logging.WARNING, outcome.undefined_skip_message)
        return

    if outcome.record_error is not None:
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {
                "access_code": outcome.access_code,
                "row": outcome.source_row,
                "reason": outcome.record_error,
            }
        )
        emit(
            logging.ERROR,
            "Processing failed for %s: %s",
            outcome.access_code,
            outcome.record_error,
        )
        return

    if outcome.stereo_issue is not None:
        report.records_with_undefined_stereochemistry += 1
        if outcome.stereo_enumerated:
            report.stereochemistry_records_enumerated += 1
        if outcome.stereo_skipped:
            report.stereochemistry_records_skipped += 1
        report.stereochemistry_issues.append(outcome.stereo_issue)

    if outcome.no_variants_reason is not None:
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {
                "access_code": outcome.access_code,
                "row": outcome.source_row,
                "reason": outcome.no_variants_reason,
            }
        )
        emit(
            logging.WARNING,
            "Skipping %s because of unresolved stereochemistry: %s",
            outcome.access_code,
            outcome.no_variants_reason,
        )
        return

    report.total_smiles_evaluated += outcome.variant_count
    report.protonation_states_generated += outcome.protonation_states_generated

    for variant in outcome.variants:
        if variant.error is not None:
            report.failures_or_skipped_entries += 1
            report.failure_details.append(
                {
                    "access_code": variant.access_code,
                    "row": outcome.source_row,
                    "reason": variant.error,
                }
            )
            emit(
                logging.ERROR,
                "Processing failed for %s: %s",
                variant.access_code,
                variant.error,
            )
            continue

        report.molecules_converted_to_3d += 1
        if variant.pm7_used:
            report.molecules_optimized_with_pm7 += 1
            if variant.preserved_files:
                report.pm7_preserved_file_count += len(variant.preserved_files)
                report.pm7_preserved_files.extend(variant.preserved_files)

        try:
            if exporter.uses_batch_export:
                batched_structures.append((variant.access_code, variant.molecule))
            else:
                exported_paths = exporter.write(variant.molecule, variant.access_code)
                _register_exported_paths(report, exported_paths, exporter.export_format)
                report.structure_records_exported += 1
        except (Mol2ExportError, StructureValidationError) as exc:
            report.failures_or_skipped_entries += 1
            report.failure_details.append(
                {
                    "access_code": variant.access_code,
                    "row": outcome.source_row,
                    "reason": str(exc),
                }
            )
            emit(
                logging.ERROR, "Processing failed for %s: %s", variant.access_code, exc
            )
            continue

        emit(
            logging.INFO,
            "Processed %s with force field %s%s%s",
            variant.access_code,
            variant.force_field or "unknown",
            f" and {variant.mopac_method}" if variant.mopac_method else "",
            f" using validation rescue {variant.validation_rescue}"
            if variant.validation_rescue
            else "",
        )
        report.per_record_timings.append(
            {"access_code": variant.access_code, "seconds": variant.seconds}
        )


def _finalize_timing(report: RunReport, wall_clock_start: float) -> None:
    report.finished_at = datetime.now(timezone.utc).isoformat()
    report.wall_clock_seconds = round(time.perf_counter() - wall_clock_start, 4)
    durations = [
        float(entry["seconds"])
        for entry in report.per_record_timings
        if isinstance(entry.get("seconds"), (int, float))
    ]
    if not durations:
        return
    report.mean_seconds_per_record = round(statistics.mean(durations), 4)
    report.median_seconds_per_record = round(statistics.median(durations), 4)
    report.fastest_seconds = round(min(durations), 4)
    report.slowest_seconds = round(max(durations), 4)
    ordered = sorted(durations)
    p95_index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    report.p95_seconds_per_record = round(ordered[p95_index], 4)
    total = sum(durations)
    if total > 0:
        report.throughput_molecules_per_minute = round(len(durations) / total * 60.0, 2)


def _write_report(report: RunReport, settings: dict[str, Any]) -> str:
    """Write the JSON audit report unless reporting is disabled in settings."""
    reporting = settings.get("reporting", {})
    if not reporting.get("enabled", True):
        return ""
    return str(write_report(report, reporting["report_dir"]))


def _register_exported_paths(
    report: RunReport, exported_paths: list[Any], export_format: str
) -> None:
    report.structure_files_written += len(exported_paths)
    report.generated_structure_files.extend(str(path) for path in exported_paths)
    if export_format == "mol2":
        report.mol2_files_written += len(exported_paths)
        report.generated_mol2_files.extend(str(path) for path in exported_paths)
    elif export_format == "pdbqt":
        report.pdbqt_files_written += len(exported_paths)
        report.generated_pdbqt_files.extend(str(path) for path in exported_paths)


def _capture_stereochemistry_resolution(
    outcome: _RecordOutcome, resolution: Any, record: Any
) -> None:
    if getattr(resolution, "undefined_center_count", 0) <= 0:
        return
    outcome.stereo_undefined_record = True
    if getattr(resolution, "variants", []):
        outcome.stereo_enumerated = True
    else:
        outcome.stereo_skipped = True
    outcome.stereo_issue = {
        "access_code": record.access_code,
        "row": record.source_row,
        "undefined_centers": resolution.undefined_center_count,
        "action": resolution.action,
        "variant_count": len(resolution.variants),
        "reason": resolution.reason or "",
    }


def _resolve_pm7_preserved_files_dir(settings: dict[str, Any]) -> str:
    configured = str(settings.get("pm7", {}).get("preserved_files_dir", "")).strip()
    if configured:
        return configured
    return str(Path(settings["export"]["output_dir"]) / "mopac_files")
