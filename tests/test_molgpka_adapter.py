"""MolGpKa protonation backend tests.

Locks in the reviewer's litmus case: piperazine at pH 7.4 must return the
mono-cation (+1), which requires the iterative titration protocol (naive
per-site Henderson-Hasselbalch would return +2).
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torch_geometric")

from rdkit import Chem

from src.protonation.molgpka_adapter import MolGpKaProtonator


def _charge(smiles: str) -> int:
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, smiles
    return Chem.GetFormalCharge(mol)


@pytest.fixture(scope="module")
def protonator() -> MolGpKaProtonator:
    return MolGpKaProtonator({"ph": 7.4, "enabled": True})


@pytest.mark.parametrize(
    "name, smiles, expected_charge",
    [
        ("piperazine", "C1CNCCN1", 1),
        ("acetic_acid", "CC(=O)O", -1),
        ("benzoic_acid", "OC(=O)c1ccccc1", -1),
        ("morpholine", "C1COCCN1", 1),
        ("ethanol", "CCO", 0),
        ("imidazole", "c1cnc[nH]1", 0),
    ],
)
def test_dominant_microstate_charges(
    protonator: MolGpKaProtonator, name: str, smiles: str, expected_charge: int
) -> None:
    result = protonator.protonate_smiles(smiles, name)
    assert _charge(result) == expected_charge, f"{name}: {result}"


def test_protonate_states_returns_single_dominant(
    protonator: MolGpKaProtonator,
) -> None:
    states = protonator.protonate_states("C1CNCCN1", "piperazine")
    assert len(states) == 1
    assert _charge(states[0]) == 1


def test_disabled_backend_is_identity() -> None:
    protonator = MolGpKaProtonator({"ph": 7.4, "enabled": False})
    assert protonator.protonate_smiles("C1CNCCN1", "piperazine") == "C1CNCCN1"
