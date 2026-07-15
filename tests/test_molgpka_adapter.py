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


@pytest.mark.parametrize(
    "name, smiles",
    [
        ("methylamine", "CN"),
        ("ethylamine", "CCN"),
        ("isopropylamine", "CC(C)N"),
        ("tert-butylamine", "CC(C)(C)N"),
        ("dimethylamine", "CNC"),
        ("trimethylamine", "CN(C)C"),
    ],
)
def test_amine_prior_fixes_small_aliphatic_amines(name: str, smiles: str) -> None:
    # MolGpKa is out-of-distribution on these (predicts pKa ~1-4 or misses the
    # site); the chemical prior recovers the expected mono-cation at pH 7.4.
    on = MolGpKaProtonator({"ph": 7.4, "enabled": True, "amine_prior": True})
    assert _charge(on.protonate_smiles(smiles, name)) == 1


def test_amine_prior_off_reproduces_the_ood_failure() -> None:
    off = MolGpKaProtonator({"ph": 7.4, "enabled": True, "amine_prior": False})
    # Without the prior, methylamine is left neutral (the documented blind spot).
    assert _charge(off.protonate_smiles("CN", "methylamine")) == 0


@pytest.mark.parametrize(
    "name, smiles, expected_charge",
    [
        # electron-withdrawing group -> genuinely low pKa, prior must NOT fire
        ("trifluoroethylamine", "NCC(F)(F)F", 0),
        # aromatic amine -> low pKa, prior must NOT fire
        ("aniline", "Nc1ccccc1", 0),
        # coupled diamine -> titration handles it, prior must NOT reintroduce +2
        ("piperazine", "C1CNCCN1", 1),
    ],
)
def test_amine_prior_does_not_break_activated_or_coupled(
    name: str, smiles: str, expected_charge: int
) -> None:
    on = MolGpKaProtonator({"ph": 7.4, "enabled": True, "amine_prior": True})
    assert _charge(on.protonate_smiles(smiles, name)) == expected_charge
