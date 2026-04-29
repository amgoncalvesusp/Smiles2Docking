from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
import uuid

from rdkit import Chem

from src.utils.models import MolecularRecord
from src.workflow import pipeline


class _FakeSource:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def load_records(self) -> list[MolecularRecord]:
        return [
            MolecularRecord(access_code="ONE_CENTER", smiles="CC(F)Cl", source_row=1),
            MolecularRecord(access_code="TWO_CENTERS", smiles="CC(F)C(Cl)Br", source_row=2),
        ]


class _FakeCleaner:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def clean_record(self, record: MolecularRecord) -> SimpleNamespace:
        return SimpleNamespace(cleaned_smiles=record.smiles, salts_removed=False)


class _FakeProtonator:
    calls: list[tuple[str, str]] = []

    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        self.calls.append((smiles, access_code))
        return smiles


class _FakeBuilder:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def build_3d(self, smiles: str, access_code: str) -> Chem.Mol:
        molecule = Chem.MolFromSmiles(smiles)
        assert molecule is not None
        return molecule


class _FakeExporter:
    uses_batch_export = False
    export_format = "mol2"

    def __init__(self, export_settings: dict, protonation_settings: dict) -> None:
        self.export_settings = export_settings
        self.protonation_settings = protonation_settings

    def write(self, molecule: Chem.Mol, access_code: str) -> list[Path]:
        return [Path(self.export_settings["output_dir"]) / f"{access_code}.mol2"]


def test_run_workflow_reports_undefined_stereochemistry_records(
    monkeypatch
) -> None:
    monkeypatch.setattr(pipeline, "SpreadsheetSource", _FakeSource)
    monkeypatch.setattr(pipeline, "SmilesCleaner", _FakeCleaner)
    monkeypatch.setattr(pipeline, "OpenBabelProtonator", _FakeProtonator)
    monkeypatch.setattr(pipeline, "StructureBuilder", _FakeBuilder)
    monkeypatch.setattr(pipeline, "StructureExporter", _FakeExporter)

    test_root = Path(__file__).resolve().parent / ".tmp" / f"pipeline_{uuid.uuid4().hex}"
    settings = {
        "input": {
            "file_path": str(test_root / "input.csv"),
            "sheet_name": None,
            "smiles_column": "smiles",
            "access_code_column": "access_code",
        },
        "processing": {
            "strict_fragment_disambiguation": True,
            "strict_stereochemistry": True,
            "single_undefined_stereocenter_only": True,
            "max_stereochemistry_variants": 16,
            "allow_post_mopac_charge_rescue": True,
        },
        "protonation": {"ph": 7.4, "enabled": True},
        "pm7": {"enabled": False},
        "structure_generation": {},
        "export": {
            "output_dir": str(test_root / "output"),
            "mode": "separate_mol2",
            "overwrite": True,
        },
        "reporting": {"report_dir": str(test_root / "reports")},
        "logging": {
            "log_dir": str(test_root / "logs"),
            "file_name": "workflow.log",
            "level": "INFO",
        },
        "ui": {"language": "en"},
    }
    logger = logging.getLogger("smiles2docking.pipeline_test")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    result = pipeline.run_workflow(settings, logger=logger)

    assert result.report.records_with_undefined_stereochemistry == 2
    assert result.report.stereochemistry_records_enumerated == 1
    assert result.report.stereochemistry_records_skipped == 1
    assert result.report.structure_records_exported == 2
    assert result.report.failures_or_skipped_entries == 1

    issue_by_code = {
        issue["access_code"]: issue for issue in result.report.stereochemistry_issues
    }
    assert issue_by_code["ONE_CENTER"]["action"] == "enumerated_single_undefined_center"
    assert issue_by_code["ONE_CENTER"]["variant_count"] == 2
    assert issue_by_code["TWO_CENTERS"]["action"] == "skipped_multiple_undefined_centers"
    assert issue_by_code["TWO_CENTERS"]["undefined_centers"] == 2
    assert any(detail["access_code"] == "TWO_CENTERS" for detail in result.report.failure_details)


class _SkipFilterSource:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def load_records(self) -> list[MolecularRecord]:
        return [
            MolecularRecord(access_code="UNDEFINED_CARBON", smiles="CC(F)Cl", source_row=1),
            MolecularRecord(access_code="UNDEFINED_NITROGEN", smiles="CCN(C)CCC", source_row=2),
            MolecularRecord(access_code="DEFINED", smiles="C[C@H](F)Cl", source_row=3),
        ]


def test_run_workflow_skips_undefined_stereochemistry_before_protonation(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "SpreadsheetSource", _SkipFilterSource)
    monkeypatch.setattr(pipeline, "SmilesCleaner", _FakeCleaner)
    monkeypatch.setattr(pipeline, "OpenBabelProtonator", _FakeProtonator)
    monkeypatch.setattr(pipeline, "StructureBuilder", _FakeBuilder)
    monkeypatch.setattr(pipeline, "StructureExporter", _FakeExporter)
    _FakeProtonator.calls = []

    test_root = Path(__file__).resolve().parent / ".tmp" / f"skip_filter_{uuid.uuid4().hex}"
    settings = {
        "input": {
            "file_path": str(test_root / "input.csv"),
            "sheet_name": None,
            "smiles_column": "smiles",
            "access_code_column": "access_code",
        },
        "processing": {
            "strict_fragment_disambiguation": True,
            "strict_stereochemistry": False,
            "single_undefined_stereocenter_only": False,
            "skip_undefined_stereo": True,
            "allow_post_mopac_charge_rescue": True,
        },
        "protonation": {"ph": 7.4, "enabled": True},
        "pm7": {"enabled": False},
        "structure_generation": {},
        "export": {
            "output_dir": str(test_root / "output"),
            "mode": "separate_mol2",
            "overwrite": True,
        },
        "reporting": {"report_dir": str(test_root / "reports")},
        "logging": {
            "log_dir": str(test_root / "logs"),
            "file_name": "workflow.log",
            "level": "INFO",
        },
        "ui": {"language": "en"},
    }
    logger = logging.getLogger("smiles2docking.skip_filter_test")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    messages: list[str] = []

    result = pipeline.run_workflow(settings, logger=logger, message_callback=messages.append)

    assert _FakeProtonator.calls == [("C[C@H](F)Cl", "DEFINED")]
    assert result.report.structure_records_exported == 1
    assert result.report.failures_or_skipped_entries == 2
    assert any(message == "Skipped: undefined stereochemistry — CC(F)Cl" for message in messages)
    assert any(message == "Skipped: undefined stereochemistry — CCN(C)CCC" for message in messages)
    assert any(
        detail["access_code"] == "UNDEFINED_CARBON"
        and detail["reason"] == "Skipped: undefined stereochemistry — CC(F)Cl"
        for detail in result.report.failure_details
    )
    assert any(
        detail["access_code"] == "UNDEFINED_NITROGEN"
        and detail["reason"] == "Skipped: undefined stereochemistry — CCN(C)CCC"
        for detail in result.report.failure_details
    )
