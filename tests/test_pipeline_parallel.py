from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest
from rdkit import Chem

from src.utils.models import MolecularRecord
from src.workflow import pipeline


class _FakeSource:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def load_records(self) -> list[MolecularRecord]:
        return [
            MolecularRecord(access_code=f"LIG_{i:03d}", smiles="CCO", source_row=i)
            for i in range(1, 7)
        ]


class _FakeCleaner:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def clean_record(self, record: MolecularRecord) -> SimpleNamespace:
        return SimpleNamespace(cleaned_smiles=record.smiles, salts_removed=False)


class _FakeProtonator:
    backend_name = "dimorphite"

    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        return smiles


class _FakeBuilder:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def build_3d(self, smiles: str, access_code: str) -> Chem.Mol:
        molecule = Chem.MolFromSmiles(smiles)
        assert molecule is not None
        molecule.SetProp("force_field", "mmff94")
        return molecule


class _FakeExporter:
    uses_batch_export = False
    export_format = "mol2"

    def __init__(self, export_settings: dict, protonation_settings: dict) -> None:
        self.export_settings = export_settings
        self.protonation_settings = protonation_settings

    def write(self, molecule: Chem.Mol, access_code: str) -> list[Path]:
        return [Path(self.export_settings["output_dir"]) / f"{access_code}.mol2"]


def _base_settings(test_root: Path, parallel: dict | None) -> dict:
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
    if parallel is not None:
        settings["parallel"] = parallel
    return settings


def _patch(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "SpreadsheetSource", _FakeSource)
    monkeypatch.setattr(pipeline, "SmilesCleaner", _FakeCleaner)
    monkeypatch.setattr(pipeline, "build_protonator", lambda settings: _FakeProtonator(settings))
    monkeypatch.setattr(pipeline, "StructureBuilder", _FakeBuilder)
    monkeypatch.setattr(pipeline, "StructureExporter", _FakeExporter)


def test_resolve_n_jobs_defaults_to_sequential() -> None:
    assert pipeline._resolve_n_jobs({}) == 1
    assert pipeline._resolve_n_jobs({"parallel": {"enabled": False, "n_jobs": -1}}) == 1
    assert pipeline._resolve_n_jobs({"parallel": {"enabled": True, "n_jobs": 4}}) == 4
    assert pipeline._resolve_n_jobs({"parallel": {"enabled": True, "n_jobs": 0}}) == 1


def test_parallel_path_matches_sequential(monkeypatch) -> None:
    pytest.importorskip("joblib")
    _patch(monkeypatch)

    seq_root = Path(__file__).resolve().parent / ".tmp" / f"seq_{uuid.uuid4().hex}"
    par_root = Path(__file__).resolve().parent / ".tmp" / f"par_{uuid.uuid4().hex}"
    logger = logging.getLogger("smiles2docking.parallel_test")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    seq = pipeline.run_workflow(_base_settings(seq_root, None), logger=logger)
    par = pipeline.run_workflow(
        _base_settings(par_root, {"enabled": True, "n_jobs": 2, "backend": "threading", "batch_size": "auto"}),
        logger=logger,
    )

    assert seq.report.n_jobs_used == 1
    assert par.report.n_jobs_used == 2
    assert par.report.structure_records_exported == seq.report.structure_records_exported == 6
    assert par.report.molecules_converted_to_3d == seq.report.molecules_converted_to_3d == 6
    # Order of exported codes preserved (records consumed in input order)
    par_names = [Path(p).name for p in par.report.generated_mol2_files]
    seq_names = [Path(p).name for p in seq.report.generated_mol2_files]
    assert par_names == seq_names
    assert par_names == [f"LIG_{i:03d}.mol2" for i in range(1, 7)]
