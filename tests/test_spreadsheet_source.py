import shutil
import uuid
from pathlib import Path

import pandas as pd

from src.database.spreadsheet_source import SpreadsheetSource
from src.utils.config import PROJECT_ROOT


def _build_settings(file_path: Path) -> dict:
    return {
        "input": {
            "file_path": str(file_path),
            "sheet_name": "Sheet1",
            "smiles_column": "smiles",
            "access_code_column": "access_code",
        }
    }


def _test_dir() -> Path:
    path = PROJECT_ROOT / "data" / "intermediate" / "test_tmp" / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_load_records_from_csv() -> None:
    tmp_path = _test_dir()
    source_file = tmp_path / "molecules.csv"
    pd.DataFrame(
        [
            {"access_code": "CMPD_001", "smiles": "CCO", "series": "A"},
            {"access_code": "CMPD_002", "smiles": "CCN", "series": "B"},
        ]
    ).to_csv(source_file, index=False)

    source = SpreadsheetSource(_build_settings(source_file))
    records = source.load_records()

    assert [record.access_code for record in records] == ["CMPD_001", "CMPD_002"]
    assert records[0].metadata["series"] == "A"
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_load_records_from_xlsx(monkeypatch) -> None:
    tmp_path = _test_dir()
    source_file = tmp_path / "molecules.xlsx"
    pd.DataFrame(
        [
            {"access_code": "CMPD_010", "smiles": "CC(=O)O"},
        ]
    ).to_excel(source_file, index=False, sheet_name="Sheet1")

    source = SpreadsheetSource(_build_settings(source_file))
    selections = iter(["Sheet1", "smiles", "access_code"])
    monkeypatch.setattr(SpreadsheetSource, "_select_column_dialog", lambda self, *args: next(selections))
    records = source.load_records()

    assert len(records) == 1
    assert records[0].smiles == "CC(=O)O"
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_load_records_from_smi_generates_sequential_ids() -> None:
    tmp_path = _test_dir()
    source_file = tmp_path / "molecules.smi"
    source_file.write_text("CCO\nCCN named_amine\nnot_smiles bad\n", encoding="utf-8")

    source = SpreadsheetSource(_build_settings(source_file))
    records = source.load_records()

    assert [record.access_code for record in records] == ["mol_001", "named_amine"]
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_load_records_from_tsv_auto_detects_columns() -> None:
    tmp_path = _test_dir()
    source_file = tmp_path / "molecules.tsv"
    pd.DataFrame(
        [
            {"compound_id": "CMPD_100", "structure": "C[C@H](F)Cl"},
            {"compound_id": "CMPD_101", "structure": "N[C@@H](C)C(=O)O"},
        ]
    ).to_csv(source_file, index=False, sep="\t")

    source = SpreadsheetSource(_build_settings(source_file))
    records = source.load_records()

    assert [record.access_code for record in records] == ["CMPD_100", "CMPD_101"]
    assert [record.smiles for record in records] == ["C[C@H](F)Cl", "N[C@@H](C)C(=O)O"]
    shutil.rmtree(tmp_path, ignore_errors=True)
