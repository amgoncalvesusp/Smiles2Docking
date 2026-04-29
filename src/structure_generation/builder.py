from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem


class StructureGenerationError(Exception):
    """Raised when 3D coordinate generation fails."""


@dataclass(slots=True)
class StructureBuilder:
    settings: dict[str, Any]

    def build_3d(self, smiles: str, access_code: str) -> Chem.Mol:
        molecule = Chem.MolFromSmiles(smiles, sanitize=True)
        if molecule is None:
            raise StructureGenerationError(f"Unable to parse protonated SMILES for {access_code!r}")

        molecule = Chem.AddHs(molecule)
        max_attempts = int(self.settings.get("max_attempts", 3))
        embedding_failures: list[str] = []
        for strategy_name, parameter_factory, attempts in self._embedding_strategies(max_attempts):
            for _ in range(attempts):
                working_copy = Chem.Mol(molecule)
                params = parameter_factory()
                if AllChem.EmbedMolecule(working_copy, params) == 0:
                    self._optimize_geometry(working_copy, access_code)
                    working_copy.SetProp("_Name", access_code)
                    working_copy.SetProp("embedding_strategy", strategy_name)
                    return working_copy
            embedding_failures.append(strategy_name)

        details = ", ".join(embedding_failures) if embedding_failures else "no embedding strategy available"
        raise StructureGenerationError(f"3D embedding failed for {access_code!r}. Attempts: {details}")

    def _optimize_geometry(self, molecule: Chem.Mol, access_code: str) -> None:
        if not self.settings.get("optimize_geometry", True):
            molecule.SetProp("force_field", "none")
            return

        preferences = self.settings.get("force_field_preference", ["mmff94", "mmff94s", "uff"])
        max_iterations = int(self.settings.get("max_optimization_iterations", 1000))
        allow_unoptimized = self.settings.get("allow_unoptimized_output", False)

        optimization_errors: list[str] = []
        for force_field_name in preferences:
            try:
                result = self._run_force_field(molecule, force_field_name, max_iterations)
            except Exception as exc:
                optimization_errors.append(f"{force_field_name}: {exc}")
                continue

            if result is None:
                optimization_errors.append(f"{force_field_name}: not parameterizable for this molecule")
                continue

            if result != 0:
                optimization_errors.append(
                    f"{force_field_name}: optimization did not converge within {max_iterations} iterations"
                )
                continue

            molecule.SetProp("force_field", force_field_name)
            return

        molecule.SetProp("force_field", "unoptimized")
        if allow_unoptimized:
            return

        details = "; ".join(optimization_errors) if optimization_errors else "no force field was applicable"
        raise StructureGenerationError(
            f"Geometry optimization failed for {access_code!r}. Attempts: {details}"
        )

    def _run_force_field(self, molecule: Chem.Mol, force_field_name: str, max_iterations: int) -> int | None:
        normalized_name = force_field_name.strip().lower()
        if normalized_name in {"mmff94", "mmff94s"}:
            properties = AllChem.MMFFGetMoleculeProperties(molecule, mmffVariant=normalized_name)
            if properties is None:
                return None
            return AllChem.MMFFOptimizeMolecule(
                molecule,
                mmffVariant=normalized_name,
                maxIters=max_iterations,
            )

        if normalized_name == "uff":
            if not AllChem.UFFHasAllMoleculeParams(molecule):
                return None
            return AllChem.UFFOptimizeMolecule(molecule, maxIters=max_iterations)

        raise StructureGenerationError(
            f"Unsupported force field '{force_field_name}'. Supported values: mmff94, mmff94s, uff."
        )

    def _embedding_strategies(self, max_attempts: int) -> list[tuple[str, Any, int]]:
        seed = int(self.settings.get("embed_seed", 61453))
        return [
            ("etkdg", lambda: self._embed_params(seed=seed, use_random_coords=False, small_ring=False), max_attempts),
            (
                "etkdg_random_coords",
                lambda: self._embed_params(seed=seed, use_random_coords=True, small_ring=False),
                max_attempts,
            ),
            (
                "sr_etkdg_random_coords",
                lambda: self._embed_params(seed=-1, use_random_coords=True, small_ring=True),
                max(1, max_attempts),
            ),
        ]

    def _embed_params(self, seed: int, use_random_coords: bool, small_ring: bool) -> Any:
        params = AllChem.srETKDGv3() if small_ring else AllChem.ETKDGv3()
        params.randomSeed = seed
        params.useRandomCoords = use_random_coords
        return params
