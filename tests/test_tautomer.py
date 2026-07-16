"""Optional tautomer step tests."""

from __future__ import annotations

import sys

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


def test_sphysnet_missing_script_is_actionable() -> None:
    taut = build_tautomerizer({"enabled": True, "backend": "sphysnet"})
    with pytest.raises(TautomerError) as excinfo:
        taut.dominant_tautomer("O=c1cccc[nH]1", "pyridone")
    assert "sPhysNet-Taut" in str(excinfo.value)


def test_sphysnet_does_not_protonate() -> None:
    # sPhysNet-Taut only selects the tautomer; protonation runs downstream.
    taut = build_tautomerizer({"enabled": True, "backend": "sphysnet"})
    assert getattr(taut, "produces_protonated", True) is False


def test_sphysnet_parse_dominant_returns_lowest_energy_neutral_tautomer() -> None:
    from src.tautomer.sphysnet_adapter import _parse_dominant

    # The dominant record is chosen by energy; its neutral 'tsmi' is returned,
    # not 'psmis' (protonation is done later by MolGpKa).
    stdout = (
        "some log line\n"
        "[{'tsmi': 'CCC(O)=CC(C)=O', 'psmis': ['[protonated]'], 'score': '0.0', "
        "'label': 'low_energy'}, {'tsmi': 'CCC(=O)CC(C)=O', 'psmis': "
        "['CCC(=O)CC(C)=O'], 'score': '0.4', 'label': 'low_energy'}]\n"
    )
    result = _parse_dominant(stdout, "CCC(=O)CC(C)=O", "L")
    assert _canon(result) == _canon("CCC(O)=CC(C)=O")


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="sPhysNet-Taut is not supported on native Windows",
)
def test_sphysnet_runs_external_script(tmp_path) -> None:
    # A stand-in for predict_tautomer.py: prints the sPhysNet-Taut record list.
    fake = tmp_path / "predict_tautomer.py"
    fake.write_text(
        "print([{'tsmi': 'CC(=O)C', 'psmis': ['CC(=O)C'], "
        "'score': '0.0', 'label': 'low_energy'}])\n",
        encoding="utf-8",
    )
    taut = build_tautomerizer(
        {
            "enabled": True,
            "backend": "sphysnet",
            "ph": 7.4,
            "sphysnet": {
                "script_path": str(fake),
                "python": sys.executable,
                "num_confs": 1,
            },
        }
    )
    result = taut.dominant_tautomer("CC(=O)C", "acetone")
    assert _canon(result) == _canon("CC(=O)C")


@pytest.mark.skipif(
    not sys.platform.startswith("win"),
    reason="Windows-only guard",
)
def test_sphysnet_blocked_on_windows() -> None:
    taut = build_tautomerizer(
        {"enabled": True, "backend": "sphysnet", "sphysnet": {"script_path": "x"}}
    )
    with pytest.raises(TautomerError) as excinfo:
        taut.dominant_tautomer("CC(=O)C", "acetone")
    assert "WSL" in str(excinfo.value)
