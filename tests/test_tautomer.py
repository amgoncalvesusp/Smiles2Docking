"""Optional tautomer step tests."""

from __future__ import annotations

import pytest
from rdkit import Chem

from src.tautomer.base import TautomerError
from src.tautomer.factory import build_tautomerizer
from src.tautomer.rdkit_adapter import RDKitTautomerizer, enumerate_tautomers


def _canon(smiles: str) -> str:
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def test_disabled_returns_none() -> None:
    assert build_tautomerizer(None) is None
    assert build_tautomerizer({"enabled": False}) is None


def test_rdkit_backend_selected() -> None:
    taut = build_tautomerizer({"enabled": True, "backend": "rdkit"})
    assert isinstance(taut, RDKitTautomerizer)


def test_unknown_backend_raises() -> None:
    with pytest.raises(TautomerError):
        build_tautomerizer({"enabled": True, "backend": "magic"})


def test_rdkit_canonicalises_enol_to_keto() -> None:
    taut = RDKitTautomerizer({})
    # Vinyl alcohol (enol) should canonicalise to acetaldehyde (keto).
    result = taut.dominant_tautomer("C=CO", "enol")
    assert _canon(result) == _canon("CC=O")


def test_enumerate_includes_both_tautomers() -> None:
    smis = {_canon(s) for s in enumerate_tautomers("C=CO", "enol", 16)}
    assert _canon("CC=O") in smis


def test_sphysnet_missing_dependency_is_actionable() -> None:
    taut = build_tautomerizer({"enabled": True, "backend": "sphysnet"})
    # 2-pyridone <-> 2-hydroxypyridine has multiple tautomers, forcing ranking.
    with pytest.raises(TautomerError) as excinfo:
        taut.dominant_tautomer("O=c1cccc[nH]1", "pyridone")
    assert "sPhysNet-Taut" in str(excinfo.value)
