from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from rdkit import Chem

from src.export.mol2_writer import StructureExporter


class _FakePdbqtConverter:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path]] = []

    def sdf_to_pdbqt(self, input_sdf: Path, output_pdbqt: Path) -> None:
        self.calls.append((input_sdf, output_pdbqt))
        output_pdbqt.write_text(
            "ROOT\n"
            "ATOM      1  C   UNL     1       0.000   0.000   0.000  0.00  0.00    -0.020 C \n"
            "ENDROOT\n"
            "TORSDOF 0\n",
            encoding="utf-8",
        )

    def sdf_to_mol2(self, input_sdf: Path, output_mol2: Path) -> None:
        raise AssertionError("PDBQT export should not call MOL2 conversion.")


@contextmanager
def workspace_tmp_dir() -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="smiles2docking_exporter_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_single_sdf_export_writes_all_records() -> None:
    with workspace_tmp_dir() as tmp_path:
        exporter = StructureExporter(
            {
                "output_dir": str(tmp_path),
                "overwrite": True,
                "mode": "single_sdf",
                "bundle_basename": "ligands_bundle",
            },
            {"obabel_binary": "obabel"},
        )

        molecules = [
            ("CMPD_001", Chem.MolFromSmiles("CCO")),
            ("CMPD_002", Chem.MolFromSmiles("CCN")),
        ]

        exported_paths = exporter.write_batch([(name, molecule) for name, molecule in molecules if molecule is not None])

        assert len(exported_paths) == 1
        output_path = exported_paths[0]
        assert output_path.name == "ligands_bundle.sdf"
        assert output_path.exists()

        supplier = Chem.SDMolSupplier(str(output_path), removeHs=False)
        names = [molecule.GetProp("_Name") for molecule in supplier if molecule is not None]
        assert names == ["CMPD_001", "CMPD_002"]


def test_separate_sdf_export_writes_one_file_per_record() -> None:
    with workspace_tmp_dir() as tmp_path:
        exporter = StructureExporter(
            {
                "output_dir": str(tmp_path),
                "overwrite": True,
                "mode": "separate_sdf",
            },
            {"obabel_binary": "obabel"},
        )

        molecule = Chem.MolFromSmiles("CCO")
        assert molecule is not None

        exported_paths = exporter.write(molecule, "CMPD_001")

        assert len(exported_paths) == 1
        output_path = exported_paths[0]
        assert output_path.name == "CMPD_001.sdf"
        assert output_path.exists()

        supplier = Chem.SDMolSupplier(str(output_path), removeHs=False)
        names = [entry.GetProp("_Name") for entry in supplier if entry is not None]
        assert names == ["CMPD_001"]


def test_separate_export_uses_optional_prefix() -> None:
    with workspace_tmp_dir() as tmp_path:
        exporter = StructureExporter(
            {
                "output_dir": str(tmp_path),
                "overwrite": True,
                "mode": "separate_sdf",
                "bundle_basename": "batch_A",
            },
            {"obabel_binary": "obabel"},
        )

        molecule = Chem.MolFromSmiles("CCO")
        assert molecule is not None

        exported_paths = exporter.write(molecule, "CMPD_001")

        assert len(exported_paths) == 1
        assert exported_paths[0].name == "batch_A_CMPD_001.sdf"


def test_separate_export_preserves_stereochemistry_variant_suffix_in_name() -> None:
    with workspace_tmp_dir() as tmp_path:
        exporter = StructureExporter(
            {
                "output_dir": str(tmp_path),
                "overwrite": True,
                "mode": "separate_sdf",
            },
            {"obabel_binary": "obabel"},
        )

        molecule = Chem.MolFromSmiles("C[C@H](F)Cl")
        assert molecule is not None

        exported_paths = exporter.write(molecule, "CHIRAL__atom2_clockwise")

        assert len(exported_paths) == 1
        assert exported_paths[0].name == "CHIRAL__atom2_clockwise.sdf"


def test_separate_pdbqt_export_writes_one_file_per_record() -> None:
    with workspace_tmp_dir() as tmp_path:
        exporter = StructureExporter(
            {
                "output_dir": str(tmp_path),
                "overwrite": True,
                "mode": "separate_pdbqt",
            },
            {"obabel_binary": "obabel"},
        )
        fake_converter = _FakePdbqtConverter()
        exporter.converter = fake_converter

        molecule = Chem.MolFromSmiles("CCO")
        assert molecule is not None

        exported_paths = exporter.write(molecule, "CMPD_001")

        assert exporter.export_format == "pdbqt"
        assert len(exported_paths) == 1
        output_path = exported_paths[0]
        assert output_path.name == "CMPD_001.pdbqt"
        assert output_path.exists()
        assert fake_converter.calls[0][0].suffix == ".sdf"
        assert "ATOM" in output_path.read_text(encoding="utf-8")


def test_single_pdbqt_export_writes_bundle() -> None:
    with workspace_tmp_dir() as tmp_path:
        exporter = StructureExporter(
            {
                "output_dir": str(tmp_path),
                "overwrite": True,
                "mode": "single_pdbqt",
                "bundle_basename": "ligands_bundle",
            },
            {"obabel_binary": "obabel"},
        )
        fake_converter = _FakePdbqtConverter()
        exporter.converter = fake_converter

        molecules = [
            ("CMPD_001", Chem.MolFromSmiles("CCO")),
            ("CMPD_002", Chem.MolFromSmiles("CCN")),
        ]

        exported_paths = exporter.write_batch([(name, molecule) for name, molecule in molecules if molecule is not None])

        assert exporter.export_format == "pdbqt"
        assert len(exported_paths) == 1
        assert exported_paths[0].name == "ligands_bundle.pdbqt"
        assert fake_converter.calls[0][0].suffix == ".sdf"
