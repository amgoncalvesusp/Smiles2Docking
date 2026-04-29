from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from rdkit import Chem

from src.utils.models import MolecularRecord


class SpreadsheetSourceError(Exception):
    """Raised when the spreadsheet input is invalid."""


LOGGER = logging.getLogger(__name__)
ID_COLUMN_CANDIDATES = {"id", "name", "compound_id", "mol_id"}


@dataclass(slots=True)
class SpreadsheetSource:
    settings: dict[str, Any]

    def load_records(self) -> list[MolecularRecord]:
        input_settings = self.settings["input"]
        file_path = Path(input_settings["file_path"])
        if not file_path.exists():
            raise SpreadsheetSourceError(f"Input file not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix in {".smi", ".txt"}:
            records = self._read_smiles_lines(file_path)
        elif suffix in {".csv", ".tsv"}:
            frame = self._read_delimited_table(file_path)
            smiles_column = self._detect_smiles_column(frame)
            access_code_column = self._detect_id_column(frame)
            records = self._records_from_frame(frame, smiles_column, access_code_column)
        elif suffix in {".xls", ".xlsx"}:
            sheet_name, smiles_column, access_code_column = self._select_excel_input(file_path)
            frame = self._read_excel_table(file_path, sheet_name)
            records = self._records_from_frame(frame, smiles_column, access_code_column)
        else:
            raise SpreadsheetSourceError(
                f"Unsupported input format '{suffix}'. Supported formats: .smi, .txt, .csv, .tsv, .xls, .xlsx."
            )

        if not records:
            message = f"No valid SMILES were loaded from {file_path}."
            self._show_error_dialog("No valid SMILES", message)
            raise SpreadsheetSourceError(message)

        return records

    def _records_from_frame(
        self,
        frame: pd.DataFrame,
        smiles_column: str,
        access_code_column: str | None,
    ) -> list[MolecularRecord]:
        records: list[MolecularRecord] = []
        for index, row in frame.iterrows():
            source_row = int(index) + 2
            raw_access_code = row.get(access_code_column, "") if access_code_column else ""
            raw_smiles = row.get(smiles_column, "")
            fallback_id = f"mol_{source_row - 1:03d}"
            access_code = fallback_id if pd.isna(raw_access_code) else str(raw_access_code).strip() or fallback_id
            smiles = "" if pd.isna(raw_smiles) else str(raw_smiles).strip()
            if not self._is_valid_smiles(smiles):
                self._log_invalid_smiles(access_code, source_row, smiles, "invalid or unparseable SMILES")
                continue
            extra = {
                key: value
                for key, value in row.to_dict().items()
                if key not in {access_code_column, smiles_column}
            }
            records.append(
                MolecularRecord(
                    access_code=access_code,
                    smiles=smiles,
                    source_row=source_row,
                    metadata=extra,
                )
            )
        return records

    def _read_smiles_lines(self, file_path: Path) -> list[MolecularRecord]:
        records: list[MolecularRecord] = []
        sequence = 1
        for source_row, raw_line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            smiles = parts[0]
            access_code = parts[1] if len(parts) >= 2 else f"mol_{sequence:03d}"
            sequence += 1
            if not self._is_valid_smiles(smiles):
                self._log_invalid_smiles(access_code, source_row, smiles, "invalid or unparseable SMILES")
                continue
            records.append(
                MolecularRecord(
                    access_code=access_code,
                    smiles=smiles,
                    source_row=source_row,
                    metadata={},
                )
            )
        return records

    def _read_delimited_table(self, file_path: Path) -> pd.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        return pd.read_csv(file_path, sep="\t")

    def _read_excel_table(self, file_path: Path, sheet_name: str) -> pd.DataFrame:
        return pd.read_excel(file_path, sheet_name=sheet_name)

    def _detect_smiles_column(self, frame: pd.DataFrame) -> str:
        candidates = [
            str(column)
            for column in frame.columns
            if self._valid_smiles_fraction(frame[column]) > 0.8
        ]
        if not candidates:
            raise SpreadsheetSourceError("Could not auto-detect a SMILES column with >80% valid non-empty values.")
        if len(candidates) == 1:
            return candidates[0]
        return self._select_column_dialog(
            "Select SMILES column",
            "Multiple columns contain valid SMILES. Select the SMILES column:",
            candidates,
        )

    def _detect_id_column(self, frame: pd.DataFrame) -> str | None:
        normalized = {str(column).strip().lower(): str(column) for column in frame.columns}
        for candidate in ("id", "name", "compound_id", "mol_id"):
            if candidate in normalized:
                return normalized[candidate]
        configured = str(self.settings["input"].get("access_code_column", "")).strip().lower()
        if configured in normalized:
            return normalized[configured]
        return None

    def _resolve_column(self, frame: pd.DataFrame, desired_name: str) -> str:
        normalized = {str(column).strip().lower(): column for column in frame.columns}
        key = desired_name.strip().lower()
        if key not in normalized:
            available = ", ".join(map(str, frame.columns))
            raise SpreadsheetSourceError(
                f"Column '{desired_name}' not found. Available columns: {available}"
            )
        return str(normalized[key])

    def _select_excel_input(self, file_path: Path) -> tuple[str, str, str]:
        workbook = pd.ExcelFile(file_path)
        if not workbook.sheet_names:
            raise SpreadsheetSourceError(f"Excel file has no sheets: {file_path}")

        sheet_name = self._select_column_dialog(
            "Select Excel sheet",
            "Select the worksheet to load:",
            workbook.sheet_names,
        )
        preview = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
        columns = [str(column) for column in preview.columns]
        if not columns:
            raise SpreadsheetSourceError(f"Excel sheet '{sheet_name}' has no header columns.")
        smiles_column = self._select_column_dialog(
            "Select SMILES column",
            "Select the SMILES column:",
            columns,
        )
        access_code_column = self._select_column_dialog(
            "Select ID column",
            "Select the molecule ID column:",
            columns,
        )
        return sheet_name, smiles_column, access_code_column

    def _select_column_dialog(self, title: str, label: str, options: list[str]) -> str:
        try:
            from PySide6.QtWidgets import QApplication, QInputDialog
        except ImportError as exc:
            raise SpreadsheetSourceError(f"{title} requires PySide6.") from exc

        if QApplication.instance() is None:
            raise SpreadsheetSourceError(f"{title} requires the GUI to be running.")
        selected, accepted = QInputDialog.getItem(None, title, label, options, 0, False)
        if not accepted or not selected:
            raise SpreadsheetSourceError(f"{title} was cancelled.")
        return str(selected)

    def _valid_smiles_fraction(self, series: pd.Series) -> float:
        values = [str(value).strip() for value in series.dropna() if str(value).strip()]
        if not values:
            return 0.0
        valid = sum(1 for value in values if self._is_valid_smiles(value))
        return valid / len(values)

    def _is_valid_smiles(self, value: str) -> bool:
        if not value:
            return False
        return Chem.MolFromSmiles(value, sanitize=True) is not None

    def _log_invalid_smiles(self, access_code: str, source_row: int, smiles: str, reason: str) -> None:
        LOGGER.warning("Skipped input row %s (%s): %s - %s", source_row, access_code, reason, smiles)

    def _show_error_dialog(self, title: str, message: str) -> None:
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
        except ImportError:
            return
        if QApplication.instance() is None:
            return
        QMessageBox.critical(None, title, message)
