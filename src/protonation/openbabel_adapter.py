from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rdkit import Chem

from src.utils.runtime import bundled_obabel_binary, openbabel_runtime_env


class OpenBabelError(Exception):
    """Raised when Open Babel execution fails."""


def _subprocess_kwargs() -> dict[str, Any]:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


@dataclass(slots=True)
class OpenBabelProtonator:
    settings: dict[str, Any]
    backend_name: str = field(default="openbabel", init=False)

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        if not self.settings.get("enabled", True):
            return smiles

        ph = str(self.settings.get("ph", 7.4))
        obabel_binary = bundled_obabel_binary(self.settings.get("obabel_binary", "obabel"))
        temp_root = self.settings.get("temp_dir")
        if temp_root:
            base_dir = Path(temp_root)
            base_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = base_dir / f"job_{uuid.uuid4().hex}"
        else:
            tmp_path = Path.cwd() / f"obabel_tmp_{uuid.uuid4().hex}"
        tmp_path.mkdir(parents=True, exist_ok=True)

        try:
            input_path = tmp_path / "input.smi"
            output_path = tmp_path / "output.smi"
            input_path.write_text(f"{smiles}\t{access_code}\n", encoding="utf-8")

            command = [
                obabel_binary,
                str(input_path),
                "-O",
                str(output_path),
                "-p",
                ph,
            ]
            self._run_command(command)

            lines = [line.strip() for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                raise OpenBabelError(f"Open Babel returned no protonated SMILES for {access_code!r}")

            candidate_smiles = self._canonicalize_smiles(lines[0].split()[0])
            if candidate_smiles is not None:
                return candidate_smiles

            fallback_smiles = self._fallback_from_structure(obabel_binary, input_path, tmp_path, ph)
            if fallback_smiles is not None:
                return fallback_smiles

            original_smiles = self._canonicalize_smiles(smiles)
            if original_smiles is not None:
                return original_smiles

            raise OpenBabelError(
                f"Unable to convert protonated output into a valid RDKit molecule for {access_code!r}"
            )
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)

    def _run_command(self, command: list[str]) -> None:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=openbabel_runtime_env(),
            **_subprocess_kwargs(),
        )
        if result.returncode != 0:
            raise OpenBabelError(result.stderr.strip() or result.stdout.strip() or "Unknown Open Babel error.")

    def _canonicalize_smiles(self, smiles: str) -> str | None:
        molecule = Chem.MolFromSmiles(smiles, sanitize=True)
        if molecule is None:
            return None
        return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)

    def _fallback_from_structure(
        self,
        obabel_binary: str,
        input_path: Path,
        temp_dir: Path,
        ph: str,
    ) -> str | None:
        sdf_path = temp_dir / "output.sdf"
        command = [
            obabel_binary,
            str(input_path),
            "-O",
            str(sdf_path),
            "-p",
            ph,
        ]
        self._run_command(command)

        try:
            supplier = Chem.SDMolSupplier(str(sdf_path), sanitize=True, removeHs=False)
        except OSError:
            return None
        for molecule in supplier:
            if molecule is None:
                continue
            try:
                molecule = Chem.RemoveHs(molecule)
            except Exception:
                pass
            smiles = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
            canonical = self._canonicalize_smiles(smiles)
            if canonical is not None:
                return canonical
        return None


@dataclass(slots=True)
class OpenBabelConverter:
    settings: dict[str, Any]

    def sdf_to_mol2(self, input_sdf: Path, output_mol2: Path) -> None:
        obabel_binary = bundled_obabel_binary(self.settings.get("obabel_binary", "obabel"))
        command = [obabel_binary, str(input_sdf), "-O", str(output_mol2)]
        self._run_conversion(command)

    def sdf_to_pdbqt(self, input_sdf: Path, output_pdbqt: Path) -> None:
        obabel_binary = bundled_obabel_binary(self.settings.get("obabel_binary", "obabel"))
        command = [
            obabel_binary,
            str(input_sdf),
            "--partialcharge",
            "gasteiger",
            "-O",
            str(output_pdbqt),
            "-xh",
        ]
        self._run_conversion(command)

    def _run_conversion(self, command: list[str]) -> None:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=openbabel_runtime_env(),
            **_subprocess_kwargs(),
        )
        if result.returncode != 0:
            raise OpenBabelError(result.stderr.strip() or result.stdout.strip() or "Unknown Open Babel error.")
