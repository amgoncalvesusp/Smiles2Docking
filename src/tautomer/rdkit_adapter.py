"""RDKit canonical-tautomer backend.

A dependency-free tautomer selector: RDKit's ``TautomerEnumerator`` enumerates
tautomers and scores them with its built-in heuristic, returning a single
canonical (dominant) tautomer. Used as the always-available tautomer backend
and as the enumeration source for the sPhysNet-Taut ranker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

from src.tautomer.base import TautomerError


def enumerate_tautomers(smiles: str, access_code: str, max_tautomers: int) -> list[str]:
    """Enumerate up to ``max_tautomers`` tautomers as canonical SMILES."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise TautomerError(
            f"Invalid SMILES for tautomer enumeration ({access_code!r}): {smiles}"
        )
    enumerator = rdMolStandardize.TautomerEnumerator()
    enumerator.SetMaxTautomers(max(1, int(max_tautomers)))
    smis = [Chem.MolToSmiles(t) for t in enumerator.Enumerate(mol)]
    unique = list(dict.fromkeys(smis))
    return unique or [Chem.MolToSmiles(mol)]


@dataclass(slots=True)
class RDKitTautomerizer:
    """Pick the RDKit canonical tautomer."""

    settings: dict[str, Any]
    backend_name: str = field(default="rdkit", init=False)

    def dominant_tautomer(self, smiles: str, access_code: str) -> str:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise TautomerError(
                f"Invalid SMILES for tautomer selection ({access_code!r}): {smiles}"
            )
        enumerator = rdMolStandardize.TautomerEnumerator()
        canonical = enumerator.Canonicalize(mol)
        return Chem.MolToSmiles(canonical)
