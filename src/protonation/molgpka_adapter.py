"""MolGpKa protonation backend (new default, v1.3.0).

MolGpKa predicts a per-atom micro-pKa on the *neutral* molecule, independently
for each ionizable site. Applying Henderson-Hasselbalch to those independent
values over-protonates molecules with coupled ionizable centres (e.g.
piperazine would come out doubly protonated at pH 7.4). To recover the true
dominant microstate this backend titrates iteratively: it protonates (or
deprotonates) the single most favourable site, then re-predicts pKa on the now
charged molecule so neighbouring sites see the updated electronic context, and
repeats until no site favours a further change.

This yields the physically ranked single dominant state the pipeline needs,
correctly returning the mono-cation for piperazine at pH 7.4.

Vendored MolGpKa inference lives in ``molgpka/`` (MIT License).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.MolStandardize import rdMolStandardize

from src.protonation.base import ProtonationError

# Guard against pathological molecules; far above any real ionizable-site count.
_MAX_TITRATION_STEPS = 12


@dataclass(slots=True)
class MolGpKaProtonator:
    """Predict the dominant protonation microstate at a target pH via MolGpKa."""

    settings: dict[str, Any]
    backend_name: str = field(default="molgpka", init=False)

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        return self.protonate_states(smiles, access_code)[0]

    def protonate_states(self, smiles: str, access_code: str) -> list[str]:
        if not self.settings.get("enabled", True):
            return [smiles]

        ph = float(self.settings.get("ph", 7.4))
        try:
            dominant = _dominant_microstate(smiles, ph)
        except ProtonationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise ProtonationError(
                f"MolGpKa failed to protonate {access_code!r}: {exc}"
            ) from exc
        return [dominant]


def _load_predictors():
    """Import the vendored MolGpKa inference lazily (torch is heavy)."""
    try:
        from src.protonation.molgpka.ionization_group import get_ionization_aid
        from src.protonation.molgpka.predict_pka import predict_acid, predict_base
    except ImportError as exc:
        raise ProtonationError(
            "MolGpKa backend unavailable: could not import its inference stack "
            f"({exc}). Ensure torch and torch-geometric are installed, or switch "
            "the protonation backend in settings."
        ) from exc
    return get_ionization_aid, predict_base, predict_acid


def _dominant_microstate(smiles: str, ph: float) -> str:
    get_ionization_aid, predict_base, predict_acid = _load_predictors()

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ProtonationError(f"MolGpKa received an invalid SMILES: {smiles!r}")

    # Start from the neutral form so titration is deterministic.
    mol = rdMolStandardize.Uncharger().uncharge(mol)
    mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    if mol is None:
        raise ProtonationError(f"MolGpKa could not neutralise SMILES: {smiles!r}")

    changed: set[int] = set()
    for _ in range(_MAX_TITRATION_STEPS):
        mol_h = AllChem.AddHs(mol)
        # Heavy-atom indices are preserved by AddHs (hydrogens are appended),
        # so indices from the H-added graph map back onto ``mol`` directly.
        base_pka = predict_base(mol_h)  # {heavy_atom_idx: pKa}
        acid_pka = predict_acid(mol_h)  # {hydrogen_idx: pKa}

        best_kind: str | None = None
        best_idx = -1
        best_score = 0.0

        for heavy_idx, pka in base_pka.items():
            if heavy_idx in changed:
                continue
            score = float(pka) - ph  # protonate a base when pKa > pH
            if score > best_score:
                best_kind, best_idx, best_score = "base", heavy_idx, score

        for h_idx, pka in acid_pka.items():
            heavy_idx = mol_h.GetAtomWithIdx(h_idx).GetNeighbors()[0].GetIdx()
            if heavy_idx in changed:
                continue
            score = ph - float(pka)  # deprotonate an acid when pKa < pH
            if score > best_score:
                best_kind, best_idx, best_score = "acid", heavy_idx, score

        if best_kind is None:
            break

        atom = mol.GetAtomWithIdx(best_idx)
        if best_kind == "base":
            _apply_charge(atom, +1)
        else:
            _apply_charge(atom, -1)
        changed.add(best_idx)
        Chem.SanitizeMol(mol)

    return Chem.MolToSmiles(mol)


def _apply_charge(atom: Chem.Atom, delta: int) -> None:
    """Add (+1) or remove (-1) one proton from a heavy atom, H-count safe.

    Uses total (implicit + explicit) hydrogen count so acids whose proton is
    implicit do not underflow ``SetNumExplicitHs`` (the upstream bug that
    crashed on carboxylic acids).
    """
    total_h = atom.GetTotalNumHs()
    atom.SetFormalCharge(atom.GetFormalCharge() + delta)
    atom.SetNoImplicit(True)
    atom.SetNumExplicitHs(max(total_h + delta, 0))
