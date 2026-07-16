"""Carbanion -> heteroatom-anion normalization (formal charge survives MOL2)."""

from __future__ import annotations

import pytest
from rdkit import Chem

from src.protonation.charge_normalization import normalize_anion_placement


def _charged(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    return [
        (a.GetSymbol(), a.GetFormalCharge())
        for a in mol.GetAtoms()
        if a.GetFormalCharge() != 0
    ]


def test_diketone_carbanion_becomes_enolate() -> None:
    result = normalize_anion_placement("CC(=O)[CH-]C(C)=O")
    # charge moved from carbon to oxygen
    assert _charged(result) == [("O", -1)]
    assert Chem.GetFormalCharge(Chem.MolFromSmiles(result)) == -1


@pytest.mark.parametrize(
    "smiles",
    [
        "CC(=O)[O-]",  # carboxylate: already on O
        "[O-]c1ccccc1",  # phenolate: already on O
        "CC[NH3+]",  # ammonium: cation untouched
        "C[N+](=O)[O-]",  # nitro: intentional charge separation kept
        "CCO",  # neutral: untouched
    ],
)
def test_no_carbanion_is_unchanged(smiles: str) -> None:
    assert normalize_anion_placement(smiles) == Chem.MolToSmiles(
        Chem.MolFromSmiles(smiles)
    )


def test_net_charge_is_conserved() -> None:
    before = Chem.GetFormalCharge(Chem.MolFromSmiles("[O-]C(=O)[CH-]C(=O)[O-]"))
    after = Chem.GetFormalCharge(
        Chem.MolFromSmiles(normalize_anion_placement("[O-]C(=O)[CH-]C(=O)[O-]"))
    )
    assert before == after == -3


def test_invalid_smiles_returned_as_is() -> None:
    assert normalize_anion_placement("not_a_smiles") == "not_a_smiles"
