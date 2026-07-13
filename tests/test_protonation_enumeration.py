"""Pipeline fan-out over protonation states (Dimorphite enumeration mode).

A backend that returns several protonation states must produce one exported
structure per state, under suffixed access codes, without disturbing the
single-state path.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from types import SimpleNamespace

from rdkit import Chem

from src.protonation.base import iter_protonation_states
from src.utils.models import MolecularRecord
from src.workflow import pipeline


class _FakeSource:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def load_records(self) -> list[MolecularRecord]:
        return [MolecularRecord(access_code="LIG_001", smiles="CCO", source_row=1)]


class _FakeCleaner:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def clean_record(self, record: MolecularRecord) -> SimpleNamespace:
        return SimpleNamespace(cleaned_smiles=record.smiles, salts_removed=False)


class _EnumeratingProtonator:
    """Returns two states so the pipeline must fan out."""

    backend_name = "dimorphite"

    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        return smiles

    def protonate_states(self, smiles: str, access_code: str) -> list[str]:
        return ["CC[O-]", "CCO"]


class _FakeBuilder:
    def __init__(self, settings: dict) -> None:
        self.settings = settings

    def build_3d(self, smiles: str, access_code: str) -> Chem.Mol:
        molecule = Chem.MolFromSmiles(smiles)
        assert molecule is not None, smiles
        molecule.SetProp("force_field", "mmff94")
        return molecule


class _FakeExporter:
    uses_batch_export = False
    export_format = "mol2"

    def __init__(self, export_settings: dict, protonation_settings: dict) -> None:
        self.export_settings = export_settings

    def write(self, molecule: Chem.Mol, access_code: str) -> list[Path]:
        return [Path(self.export_settings["output_dir"]) / f"{access_code}.mol2"]


def _settings(root: Path) -> dict:
    return {
        "input": {
            "file_path": str(root / "input.csv"),
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
        "protonation": {"ph": 7.4, "enabled": True, "backend": "dimorphite"},
        "pm7": {"enabled": False},
        "structure_generation": {},
        "export": {
            "output_dir": str(root / "output"),
            "mode": "separate_mol2",
            "overwrite": True,
        },
        "reporting": {"report_dir": str(root / "reports")},
        "logging": {
            "log_dir": str(root / "logs"),
            "file_name": "workflow.log",
            "level": "INFO",
        },
        "ui": {"language": "en"},
    }


def test_iter_protonation_states_fallback_single() -> None:
    class _SingleOnly:
        def protonate_smiles(self, smiles: str, access_code: str) -> str:
            return smiles + "X"

    assert iter_protonation_states(_SingleOnly(), "CCO", "L") == ["CCOX"]


def test_iter_protonation_states_uses_enumeration() -> None:
    states = iter_protonation_states(_EnumeratingProtonator({}), "CCO", "L")
    assert states == ["CC[O-]", "CCO"]


def test_pipeline_fans_out_over_states(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "SpreadsheetSource", _FakeSource)
    monkeypatch.setattr(pipeline, "SmilesCleaner", _FakeCleaner)
    monkeypatch.setattr(
        pipeline, "build_protonator", lambda s: _EnumeratingProtonator(s)
    )
    monkeypatch.setattr(pipeline, "StructureBuilder", _FakeBuilder)
    monkeypatch.setattr(pipeline, "StructureExporter", _FakeExporter)

    root = Path(__file__).resolve().parent / ".tmp" / f"enum_{uuid.uuid4().hex}"
    logger = logging.getLogger("smiles2docking.enum_test")
    logger.handlers.clear()

    result = pipeline.run_workflow(_settings(root), logger=logger)
    report = result.report

    assert report.protonation_states_generated == 2
    assert report.structure_records_exported == 2
    names = sorted(Path(p).name for p in report.generated_mol2_files)
    assert names == ["LIG_001_p1.mol2", "LIG_001_p2.mol2"]
