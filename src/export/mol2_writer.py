from __future__ import annotations

import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rdkit import Chem

from src.export.pdbqt_writer import PDBQTExportError, PDBQTWriter
from src.protonation.openbabel_adapter import OpenBabelConverter


class Mol2ExportError(Exception):
    """Raised when structure export fails."""


EXPORT_FORMAT_BY_MODE = {
    "separate_mol2": "mol2",
    "single_mol2": "mol2",
    "separate_sdf": "sdf",
    "single_sdf": "sdf",
    "separate_pdbqt": "pdbqt",
    "single_pdbqt": "pdbqt",
}

SINGLE_FILE_MODES = {"single_mol2", "single_sdf", "single_pdbqt"}


@dataclass(slots=True)
class StructureExporter:
    export_settings: dict[str, Any]
    protonation_settings: dict[str, Any]
    converter: OpenBabelConverter = field(init=False)
    pdbqt_writer: PDBQTWriter | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.converter = OpenBabelConverter(self.protonation_settings)

    def _ensure_pdbqt_writer(self) -> PDBQTWriter:
        if self.pdbqt_writer is None:
            self.pdbqt_writer = PDBQTWriter(dict(self.export_settings.get("pdbqt", {})))
        return self.pdbqt_writer

    @property
    def mode(self) -> str:
        return str(self.export_settings.get("mode", "separate_mol2"))

    @property
    def export_format(self) -> str:
        return EXPORT_FORMAT_BY_MODE.get(self.mode, "mol2")

    @property
    def uses_batch_export(self) -> bool:
        return self.mode in SINGLE_FILE_MODES

    def write(self, molecule: Chem.Mol, access_code: str) -> list[Path]:
        if self.uses_batch_export:
            raise Mol2ExportError("Batch export mode requires write_batch().")

        output_dir = Path(self.export_settings["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._separate_output_path(output_dir, access_code)
        safe_name = output_path.stem
        self._ensure_writable(output_path)

        if self.mode == "separate_sdf":
            self._write_sdf_records([(access_code, molecule)], output_path)
            return [output_path]

        if self.mode == "separate_pdbqt":
            self._write_pdbqt_one(molecule, output_path, access_code)
            return [output_path]

        with self._temporary_dir(output_dir) as tmp_path:
            sdf_path = tmp_path / f"{safe_name}.sdf"
            self._write_sdf_records([(access_code, molecule)], sdf_path)
            self._convert_sdf_to_mol2(sdf_path, output_path, access_code)

        return [output_path]

    def write_batch(self, molecules: list[tuple[str, Chem.Mol]]) -> list[Path]:
        if not molecules:
            return []
        if not self.uses_batch_export:
            exported_paths: list[Path] = []
            for access_code, molecule in molecules:
                exported_paths.extend(self.write(molecule, access_code))
            return exported_paths

        output_dir = Path(self.export_settings["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        bundle_name = self._resolved_bundle_name()

        if self.mode == "single_sdf":
            output_path = output_dir / f"{bundle_name}.sdf"
            self._ensure_writable(output_path)
            self._write_sdf_records(molecules, output_path)
            return [output_path]

        if self.mode == "single_mol2":
            output_path = output_dir / f"{bundle_name}.mol2"
            self._ensure_writable(output_path)
            with self._temporary_dir(output_dir) as tmp_path:
                sdf_path = tmp_path / f"{bundle_name}.sdf"
                self._write_sdf_records(molecules, sdf_path)
                self._convert_sdf_to_mol2(sdf_path, output_path, bundle_name)
            return [output_path]

        if self.mode == "single_pdbqt":
            output_path = output_dir / f"{bundle_name}.pdbqt"
            self._ensure_writable(output_path)
            self._write_pdbqt_batch(molecules, output_path, bundle_name)
            return [output_path]

        raise Mol2ExportError(f"Unsupported export mode: {self.mode}")

    def _write_sdf_records(
        self, molecules: list[tuple[str, Chem.Mol]], output_path: Path
    ) -> None:
        # RDKit's SDWriter opens files through narrow-char C++ I/O that cannot
        # encode non-ASCII paths on Windows (e.g. OneDrive folders with accented
        # names), failing with "Bad output file". Stage the write on an
        # ASCII-safe temp path, then move it into place with Python's
        # Unicode-safe file API.
        fd, tmp_name = tempfile.mkstemp(suffix=".sdf")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            writer = Chem.SDWriter(str(tmp_path))
            if writer is None:
                raise Mol2ExportError(f"Could not create SDF writer for {output_path}")
            try:
                for access_code, molecule in molecules:
                    export_molecule = Chem.Mol(molecule)
                    export_molecule.SetProp("_Name", access_code)
                    writer.write(export_molecule)
            finally:
                writer.close()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()
            shutil.move(str(tmp_path), str(output_path))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def _convert_sdf_to_mol2(
        self, input_sdf: Path, output_mol2: Path, label: str
    ) -> None:
        try:
            self.converter.sdf_to_mol2(input_sdf, output_mol2)
        except Exception as exc:
            raise Mol2ExportError(f"Could not export {label!r} to MOL2: {exc}") from exc

    def _write_pdbqt_one(
        self, molecule: Chem.Mol, output_pdbqt: Path, label: str
    ) -> None:
        try:
            self._ensure_pdbqt_writer().write_one(molecule, output_pdbqt, label)
        except PDBQTExportError as exc:
            raise Mol2ExportError(
                f"Could not export {label!r} to PDBQT: {exc}"
            ) from exc

    def _write_pdbqt_batch(
        self, molecules: list[tuple[str, Chem.Mol]], output_pdbqt: Path, label: str
    ) -> None:
        try:
            self._ensure_pdbqt_writer().write_batch(molecules, output_pdbqt)
        except PDBQTExportError as exc:
            raise Mol2ExportError(
                f"Could not export {label!r} to PDBQT: {exc}"
            ) from exc

    def _ensure_writable(self, output_path: Path) -> None:
        if output_path.exists() and not self.export_settings.get("overwrite", True):
            raise Mol2ExportError(f"Output file already exists: {output_path}")

    def _sanitize_filename(self, value: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
        return sanitized or "unnamed_record"

    def _resolved_bundle_name(self) -> str:
        raw_value = str(self.export_settings.get("bundle_basename", "")).strip()
        if not raw_value:
            raw_value = "prepared_ligands"
        return self._sanitize_filename(raw_value)

    def _separate_output_path(self, output_dir: Path, access_code: str) -> Path:
        prefix = str(self.export_settings.get("bundle_basename", "")).strip()
        safe_name = self._sanitize_filename(access_code)
        if prefix:
            safe_name = f"{self._sanitize_filename(prefix)}_{safe_name}"
        suffix_by_format = {"sdf": ".sdf", "pdbqt": ".pdbqt", "mol2": ".mol2"}
        suffix = suffix_by_format[self.export_format]
        return output_dir / f"{safe_name}{suffix}"

    def _temporary_dir(self, output_dir: Path) -> "_TemporaryDirectory":
        return _TemporaryDirectory(self.export_settings.get("temp_dir"), output_dir)


@dataclass(slots=True)
class _TemporaryDirectory:
    configured_root: str | None
    fallback_root: Path
    path: Path | None = None

    def __enter__(self) -> Path:
        if self.configured_root:
            base_dir = Path(self.configured_root)
            base_dir.mkdir(parents=True, exist_ok=True)
            self.path = base_dir / f"job_{uuid.uuid4().hex}"
        else:
            self.path = self.fallback_root / f"export_tmp_{uuid.uuid4().hex}"
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.path is not None:
            shutil.rmtree(self.path, ignore_errors=True)


Mol2Exporter = StructureExporter
