from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rdkit import Chem

from src.protonation.openbabel_adapter import OpenBabelError, OpenBabelProtonator
from src.structure_generation.builder import StructureBuilder, StructureGenerationError
from src.utils.config import load_settings, resolve_settings_paths


CASES = [
    ("EOS102005", "COC(=O)C1=COC(C)C2CN3CCc4c([nH]c5ccccc45)C3CC12"),
    ("EOS100686", "COc1ccc(C2C(C#N)=C(N)OC3=C2C(=O)CC(c2cccc4ccccc24)C3)cc1"),
    ("EOS100876", "Cc1cccc2c3c(ccc12)C1=C(C(=O)C3=O)[C@@H](C)CO1"),
    ("EOS100880", "C[C@H]1COC2=C1C(=O)C(=O)c1c2ccc2c1CCCC2(C)C"),
    ("EOS100960", "CC1(C)CCC2=C(O1)c1ccccc1C(=O)C2=O"),
    (
        "EOS101026",
        "CN1Cc2c(Cl)cc(Cl)cc2[C@H](c2cccc(S(=O)(=O)NCCOCCOCCNC(=O)NCCCCNC(=O)NCCOCCOCCNS(=O)(=O)c3cccc([C@@H]4CN(C)Cc5c(Cl)cc(Cl)cc54)c3)c2)C1",
    ),
    ("EOS101078", "CCOc1nc2cccc(C(=O)O)c2n1Cc1ccc(-c2ccccc2-c2nn[nH]n2)cc1"),
]


def main() -> int:
    settings = resolve_settings_paths(load_settings())
    protonator = OpenBabelProtonator(settings["protonation"])
    builder = StructureBuilder(settings["structure_generation"])

    for access_code, smiles in CASES:
        print("=" * 88)
        print(access_code)
        print(f"input: {smiles}")
        initial = Chem.MolFromSmiles(smiles, sanitize=True)
        print(f"rdkit_input_parse: {'ok' if initial is not None else 'fail'}")

        try:
            protonated = protonator.protonate_smiles(smiles, access_code)
            print(f"protonated: {protonated}")
        except OpenBabelError as exc:
            print(f"openbabel_error: {exc}")
            continue

        parsed = Chem.MolFromSmiles(protonated, sanitize=True)
        print(f"rdkit_protonated_parse: {'ok' if parsed is not None else 'fail'}")
        if parsed is not None:
            print(f"canonical: {Chem.MolToSmiles(parsed, canonical=True)}")

        try:
            builder.build_3d(protonated, access_code)
            print("embed: ok")
        except StructureGenerationError as exc:
            print(f"embed_error: {exc}")
        except Exception as exc:
            print(f"unexpected_builder_error: {type(exc).__name__}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
