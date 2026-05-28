from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rdkit import Chem
from rdkit.Chem import AllChem


SMILES = "C[NH+]1Cc2c(Cl)cc(Cl)cc2[C@H](c2cccc(S(=O)(=O)NCCOCCOCCNC(=O)NCCCCNC(=O)NCCOCCOCCNS(=O)(=O)c3cccc([C@@H]4C[NH+](C)Cc5c(Cl)cc(Cl)cc54)c3)c2)C1"


def try_embed(name: str, params: AllChem.EmbedParameters, attempts: int = 1) -> None:
    mol = Chem.AddHs(Chem.MolFromSmiles(SMILES))
    if mol is None:
        print("parse failed")
        return
    for idx in range(attempts):
        working = Chem.Mol(mol)
        result = AllChem.EmbedMolecule(working, params)
        if result == 0:
            print(f"{name}: success on attempt {idx + 1}")
            return
    print(f"{name}: failed after {attempts} attempts")


def main() -> int:
    print(f"heavy_atoms={Chem.MolFromSmiles(SMILES).GetNumHeavyAtoms()}")

    p1 = AllChem.ETKDGv3()
    p1.randomSeed = 61453
    try_embed("ETKDGv3_default", p1, attempts=10)

    p2 = AllChem.ETKDGv3()
    p2.randomSeed = 61453
    p2.useRandomCoords = True
    try_embed("ETKDGv3_random_coords", p2, attempts=10)

    p3 = AllChem.srETKDGv3()
    p3.randomSeed = 61453
    p3.useRandomCoords = True
    try_embed("srETKDGv3_random_coords", p3, attempts=10)

    p4 = AllChem.ETKDGv3()
    p4.randomSeed = -1
    p4.useRandomCoords = True
    try_embed("ETKDGv3_random_seed_random_coords", p4, attempts=20)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
