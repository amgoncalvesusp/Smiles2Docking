from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from rdkit import Chem
import pytest

from src.protonation.openbabel_adapter import OpenBabelProtonator


def _formal_charge(smiles: str) -> int:
    molecule = Chem.MolFromSmiles(smiles)
    assert molecule is not None
    return sum(atom.GetFormalCharge() for atom in molecule.GetAtoms())


def test_protonator_changes_charge_state_with_ph() -> None:
    low_ph = OpenBabelProtonator({"enabled": True, "ph": 2.0, "obabel_binary": "obabel"})
    high_ph = OpenBabelProtonator({"enabled": True, "ph": 12.0, "obabel_binary": "obabel"})

    acetic_low = low_ph.protonate_smiles("CC(=O)O", "ACID")
    acetic_high = high_ph.protonate_smiles("CC(=O)O", "ACID")
    methylamine_low = low_ph.protonate_smiles("CN", "BASE")
    methylamine_high = high_ph.protonate_smiles("CN", "BASE")

    assert _formal_charge(acetic_low) == 0
    assert _formal_charge(acetic_high) == -1
    assert _formal_charge(methylamine_low) == 1
    assert _formal_charge(methylamine_high) == 0


def test_invalid_protonated_smiles_falls_back_to_structure_output(monkeypatch: pytest.MonkeyPatch) -> None:
    protonator = OpenBabelProtonator({"enabled": True, "ph": 7.4, "obabel_binary": "obabel"})

    def fake_run(command, **kwargs):
        output_path = Path(command[command.index("-O") + 1])
        if output_path.suffix == ".smi":
            output_path.write_text("C1=C[O-]1 BAD\n", encoding="utf-8")
        else:
            mol = Chem.MolFromSmiles("C[NH3+]")
            assert mol is not None
            output_path.write_text(Chem.MolToMolBlock(mol) + "\n$$$$\n", encoding="utf-8")

        class Result:
            returncode = 0
            stderr = ""
            stdout = ""

        return Result()

    monkeypatch.setattr("src.protonation.openbabel_adapter.subprocess.run", fake_run)

    protonated = protonator.protonate_smiles("CN", "BASE")

    assert _formal_charge(protonated) == 1


def test_invalid_protonated_outputs_fall_back_to_original_smiles(monkeypatch: pytest.MonkeyPatch) -> None:
    protonator = OpenBabelProtonator({"enabled": True, "ph": 7.4, "obabel_binary": "obabel"})

    def fake_run(command, **kwargs):
        output_path = Path(command[command.index("-O") + 1])
        if output_path.suffix == ".smi":
            output_path.write_text("C1=C[O-]1 BAD\n", encoding="utf-8")
        else:
            output_path.write_text("", encoding="utf-8")

        class Result:
            returncode = 0
            stderr = ""
            stdout = ""

        return Result()

    monkeypatch.setattr("src.protonation.openbabel_adapter.subprocess.run", fake_run)

    protonated = protonator.protonate_smiles("CCO", "ALCOHOL")

    assert Chem.MolToSmiles(Chem.MolFromSmiles(protonated), canonical=True) == Chem.MolToSmiles(
        Chem.MolFromSmiles("CCO"), canonical=True
    )
