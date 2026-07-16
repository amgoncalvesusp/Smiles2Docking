"""Move carbon-centred anions onto adjacent heteroatoms after (de)protonation.

MolGpKa (and rule-based backends) can deprotonate an acidic C-H directly, giving
a carbanion, for example the enol(ate)-forming central C-H of a 1,3-diketone,
which is returned as ``CC(=O)[CH-]C(C)=O``. The chemically dominant form is the
enolate, with the negative charge on oxygen (``CC(=O)C=C(C)[O-]``). Beyond being
the correct representation, this matters for export: the SYBYL atom types used by
MOL2 cannot encode a formal charge on carbon, so a carbanion is written with no
charge at all, whereas an oxygen (or nitrogen) anion is preserved.

``normalize_anion_placement`` selects, among the resonance structures of the
molecule, the one that minimises carbon-centred negative charge. It is a no-op
for molecules without a carbanion, so structures that are already correct are
returned unchanged.
"""

from __future__ import annotations

from rdkit import Chem

# Resonance enumeration is only triggered when a carbanion is present (rare), and
# a small cap keeps it bounded for large conjugated systems.
_MAX_RESONANCE_STRUCTURES = 8


def _carbanion_count(mol: Chem.Mol) -> int:
    return sum(
        1
        for atom in mol.GetAtoms()
        if atom.GetSymbol() == "C" and atom.GetFormalCharge() < 0
    )


def normalize_anion_placement(smiles: str) -> str:
    """Return ``smiles`` with any carbanion moved onto an adjacent heteroatom.

    The net charge is conserved (resonance structures share it). Molecules
    without a carbanion are returned unchanged.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return smiles
    if _carbanion_count(mol) == 0:
        return smiles

    best = mol
    best_score = _carbanion_count(mol)
    try:
        supplier = Chem.ResonanceMolSupplier(
            mol, Chem.ALLOW_CHARGE_SEPARATION, maxStructs=_MAX_RESONANCE_STRUCTURES
        )
        for resonance in supplier:
            if resonance is None:
                continue
            try:
                Chem.SanitizeMol(resonance)
            except Exception:
                continue
            score = _carbanion_count(resonance)
            if score < best_score:
                best, best_score = resonance, score
                if best_score == 0:
                    break
    except Exception:
        return Chem.MolToSmiles(mol)

    return Chem.MolToSmiles(best)
