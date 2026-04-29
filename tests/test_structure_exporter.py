from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from rdkit import Chem

from src.export.mol2_writer import StructureExporter


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
