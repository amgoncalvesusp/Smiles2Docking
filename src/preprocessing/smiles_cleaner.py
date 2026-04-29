from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rdkit import Chem

from src.utils.models import MolecularRecord


class InvalidSmilesError(Exception):
    """Raised when a SMILES string cannot be parsed."""


class AmbiguousFragmentError(Exception):
    """Raised when the principal fragment cannot be selected safely."""


@dataclass(slots=True)
class CleanResult:
    cleaned_smiles: str
    salts_removed: bool
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SmilesCleaner:
    settings: dict[str, Any]

    def clean_record(self, record: MolecularRecord) -> CleanResult:
        raw_smiles = (record.smiles or "").strip()
        if not raw_smiles:
            raise InvalidSmilesError(f"Empty SMILES for record {record.access_code!r}")

        fragments = [fragment for fragment in raw_smiles.split(".") if fragment]
        if not fragments:
            raise InvalidSmilesError(f"No valid fragment found for record {record.access_code!r}")

        salts_removed = len(fragments) > 1
        principal_smiles = (
            self._select_principal_fragment(fragments, record.access_code)
            if len(fragments) > 1
            else fragments[0]
        )
        molecule = Chem.MolFromSmiles(principal_smiles, sanitize=True)
        if molecule is None:
            raise InvalidSmilesError(
                f"Could not parse SMILES for record {record.access_code!r}: {principal_smiles}"
            )

        cleaned_smiles, kekule_preserved = self._serialize_molecule(molecule)
        notes: list[str] = []
        if salts_removed:
            notes.append("Disconnected fragments removed before downstream processing.")
        if kekule_preserved:
            notes.append("Kekule representation preserved in exported SMILES.")
        return CleanResult(cleaned_smiles=cleaned_smiles, salts_removed=salts_removed, notes=notes)

    def _select_principal_fragment(self, fragments: list[str], access_code: str) -> str:
        scored_fragments: dict[str, tuple[tuple[int, int, int, int], str]] = {}
        for fragment in fragments:
            molecule = Chem.MolFromSmiles(fragment, sanitize=True)
            if molecule is None:
                continue
            canonical_fragment = Chem.MolToSmiles(molecule, canonical=True)
            score = self._fragment_score(molecule)
            existing = scored_fragments.get(canonical_fragment)
            if existing is None or score > existing[0]:
                scored_fragments[canonical_fragment] = (score, fragment)

        if not scored_fragments:
            raise InvalidSmilesError(f"All fragments are invalid for record {access_code!r}")

        ranked_fragments = sorted(scored_fragments.values(), reverse=True)
        best_score, best_fragment = ranked_fragments[0]
        if (
            self.settings.get("strict_fragment_disambiguation", True)
            and len(ranked_fragments) > 1
            and ranked_fragments[1][0] == best_score
        ):
            raise AmbiguousFragmentError(
                "Ambiguous principal fragment for "
                f"{access_code!r}. Candidate fragments: {', '.join(fragment for _, fragment in ranked_fragments)}"
            )
        return best_fragment

    def _fragment_score(self, molecule: Chem.Mol) -> tuple[int, int, int, int]:
        carbon_atoms = sum(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms())
        heavy_atoms = molecule.GetNumHeavyAtoms()
        formal_charge = abs(Chem.GetFormalCharge(molecule))
        organic_bonus = 1 if carbon_atoms > 0 else 0
        return organic_bonus, heavy_atoms, carbon_atoms, -formal_charge

    def _serialize_molecule(self, molecule: Chem.Mol) -> tuple[str, bool]:
        if self.settings.get("preserve_kekule", True):
            kekule_molecule = Chem.Mol(molecule)
            try:
                Chem.Kekulize(kekule_molecule, clearAromaticFlags=False)
                return Chem.MolToSmiles(kekule_molecule, kekuleSmiles=True), True
            except Exception:
                pass
        return Chem.MolToSmiles(molecule, canonical=True), False
