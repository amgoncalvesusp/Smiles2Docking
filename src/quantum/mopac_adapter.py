from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rdkit import Chem
from rdkit.Geometry import Point3D

from src.quantum.mopac_methods import normalize_mopac_method
from src.utils.models import MopacOptimizationResult
from src.utils.runtime import bundled_mopac_binary


class MopacError(Exception):
    """Raised when a MOPAC PM7 calculation fails."""


def _subprocess_kwargs() -> dict[str, Any]:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


@dataclass(slots=True)
class MopacOptimizer:
    settings: dict[str, Any]

    def optimize(self, molecule: Chem.Mol, access_code: str) -> MopacOptimizationResult:
        binary = bundled_mopac_binary(
            configured_path=self.settings.get("binary_path"),
            default_binary=str(self.settings.get("binary_name", "mopac")),
        )
        charge, charge_source, reconciliation_note = self._reconcile_charge(molecule)
        temp_dir = self._create_temp_dir()
        job_stem = self._job_stem()
        input_path = temp_dir / f"{job_stem}.mop"
        keywords = self._build_keywords(charge)
        preserved_files: list[str] = []

        try:
            input_path.write_text(self._render_input(molecule, access_code, keywords), encoding="utf-8")
            try:
                result = subprocess.run(
                    [binary, input_path.name],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    **_subprocess_kwargs(),
                )
            except FileNotFoundError as exc:
                raise MopacError(
                    f"MOPAC executable not found. Configure the binary path or install MOPAC. "
                    f"Attempted command: {binary}"
                ) from exc
            except OSError as exc:
                raise MopacError(f"Could not execute MOPAC for {access_code!r}: {exc}") from exc
            if result.returncode != 0:
                raise MopacError(result.stderr.strip() or result.stdout.strip() or "Unknown MOPAC error.")

            arc_path = input_path.with_suffix(".arc")
            out_path = input_path.with_suffix(".out")
            if not arc_path.exists():
                raise MopacError(f"MOPAC did not create an ARC file for {access_code!r}")

            arc_text = arc_path.read_text(encoding="utf-8", errors="replace")
            geometry = self._parse_final_geometry(arc_text)
            heat = self._parse_heat_of_formation(arc_text)

            if not geometry and out_path.exists():
                geometry = self._parse_cartesian_coordinates(out_path.read_text(encoding="utf-8", errors="replace"))
            if not geometry:
                raise MopacError(f"Could not parse optimized geometry for {access_code!r}")

            optimized = self._apply_geometry(molecule, geometry, access_code)
            method = normalize_mopac_method(self.settings.get("method", "PM7"))
            optimized.SetProp("mopac_method", method)
            optimized.SetProp("mopac_charge", str(charge))
            optimized.SetProp("mopac_charge_source", charge_source)
            optimized.SetProp("mopac_keywords", keywords)
            optimized.SetProp("geometry_optimizer", method.lower())
            if reconciliation_note:
                optimized.SetProp("mopac_charge_reconciliation", reconciliation_note)
            if heat is not None:
                optimized.SetProp("heat_of_formation_kcal_mol", f"{heat:.6f}")
            if self.settings.get("preserve_files", False):
                preserved_files = self._preserve_artifacts(temp_dir, access_code)

            return MopacOptimizationResult(
                molecule=optimized,
                charge=charge,
                keywords=keywords,
                heat_of_formation_kcal_mol=heat,
                preserved_files=preserved_files,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _create_temp_dir(self) -> Path:
        temp_root = self.settings.get("temp_dir")
        if temp_root:
            base_dir = Path(temp_root)
            base_dir.mkdir(parents=True, exist_ok=True)
            path = base_dir / f"job_{uuid.uuid4().hex}"
        else:
            path = Path.cwd() / f"mopac_tmp_{uuid.uuid4().hex}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _job_stem(self) -> str:
        return f"mopac_{uuid.uuid4().hex[:12]}"

    def _build_keywords(self, charge: int) -> str:
        parts = [normalize_mopac_method(self.settings.get("method", "PM7"))]
        if self.settings.get("use_mmok", True):
            parts.append("MMOK")
        parts.append("OPT")
        parts.append("XYZ")
        parts.append(f"CHARGE={charge}")
        if self.settings.get("use_eps", True):
            parts.append(f"EPS={float(self.settings.get('eps', 78.39)):.2f}")
        return " ".join(parts)

    def _render_input(self, molecule: Chem.Mol, access_code: str, keywords: str) -> str:
        if molecule.GetNumConformers() == 0:
            raise MopacError(f"No 3D coordinates available for {access_code!r}")
        conformer = molecule.GetConformer()
        lines = [keywords, access_code, "Generated by SMILES2Docking"]
        for atom in molecule.GetAtoms():
            position = conformer.GetAtomPosition(atom.GetIdx())
            lines.append(
                f"{atom.GetSymbol():<2} {position.x: .8f} 1 {position.y: .8f} 1 {position.z: .8f} 1"
            )
        lines.append("")
        return "\n".join(lines)

    def _net_charge(self, molecule: Chem.Mol) -> int:
        return int(sum(atom.GetFormalCharge() for atom in molecule.GetAtoms()))

    def _reconcile_charge(self, molecule: Chem.Mol) -> tuple[int, str, str]:
        formal_charge = self._net_charge(molecule)
        serialized_charge = self._serialized_charge_from_molblock(molecule)
        if serialized_charge is None:
            return formal_charge, "formal_charge", ""
        if serialized_charge == formal_charge:
            return formal_charge, "formal_charge_and_molblock", ""
        return (
            formal_charge,
            "formal_charge_preferred",
            f"formal_charge={formal_charge}; molblock_charge={serialized_charge}",
        )

    def _serialized_charge_from_molblock(self, molecule: Chem.Mol) -> int | None:
        total_charge = 0
        found_charge_line = False
        for line in Chem.MolToMolBlock(molecule).splitlines():
            if not line.startswith("M  CHG"):
                continue
            values = [int(token) for token in re.findall(r"-?\d+", line)]
            if len(values) < 3:
                continue
            found_charge_line = True
            total_charge += sum(values[2::2])
        return total_charge if found_charge_line else None

    def _parse_final_geometry(self, arc_text: str) -> list[tuple[str, float, float, float]]:
        lines = arc_text.splitlines()
        try:
            start = next(index for index, line in enumerate(lines) if line.strip() == "FINAL GEOMETRY OBTAINED")
        except StopIteration:
            return []

        geometry: list[tuple[str, float, float, float]] = []
        atom_pattern = re.compile(
            r"^\s*([A-Za-z]{1,3})\s+([+-]?\d+(?:\.\d+)?)\s+[+-]?\d+\s+([+-]?\d+(?:\.\d+)?)\s+[+-]?\d+\s+([+-]?\d+(?:\.\d+)?)\s+[+-]?\d+\s*$"
        )
        for line in lines[start + 4 :]:
            if not line.strip():
                break
            match = atom_pattern.match(line)
            if match:
                geometry.append(
                    (
                        match.group(1),
                        float(match.group(2)),
                        float(match.group(3)),
                        float(match.group(4)),
                    )
                )
        return geometry

    def _parse_cartesian_coordinates(self, out_text: str) -> list[tuple[str, float, float, float]]:
        sections = out_text.split("CARTESIAN COORDINATES")
        if len(sections) < 2:
            return []
        last_section = sections[-1]
        geometry: list[tuple[str, float, float, float]] = []
        atom_pattern = re.compile(
            r"^\s*\d+\s+([A-Za-z]{1,3})\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s*$"
        )
        for line in last_section.splitlines():
            match = atom_pattern.match(line)
            if match:
                geometry.append(
                    (
                        match.group(1),
                        float(match.group(2)),
                        float(match.group(3)),
                        float(match.group(4)),
                    )
                )
        return geometry

    def _parse_heat_of_formation(self, arc_text: str) -> float | None:
        match = re.search(r"HEAT OF FORMATION\s*=\s*([+-]?\d+(?:\.\d+)?)\s+KCAL/MOL", arc_text)
        if match is None:
            return None
        return float(match.group(1))

    def _apply_geometry(
        self,
        molecule: Chem.Mol,
        geometry: list[tuple[str, float, float, float]],
        access_code: str,
    ) -> Chem.Mol:
        if len(geometry) != molecule.GetNumAtoms():
            raise MopacError(
                f"Optimized geometry for {access_code!r} has {len(geometry)} atoms, expected {molecule.GetNumAtoms()}."
            )

        optimized = Chem.Mol(molecule)
        conformer = optimized.GetConformer()
        for atom_index, (symbol, x, y, z) in enumerate(geometry):
            if optimized.GetAtomWithIdx(atom_index).GetSymbol() != symbol:
                raise MopacError(
                    f"Atom mismatch in optimized geometry for {access_code!r}: expected "
                    f"{optimized.GetAtomWithIdx(atom_index).GetSymbol()}, found {symbol}."
                )
            conformer.SetAtomPosition(atom_index, Point3D(x, y, z))
        optimized.SetProp("_Name", access_code)
        return optimized

    def _preserve_artifacts(self, temp_dir: Path, access_code: str) -> list[str]:
        target_root = self.settings.get("preserved_files_dir")
        if not target_root:
            raise MopacError("MOPAC file preservation was requested, but no target directory was configured.")

        destination = Path(target_root) / self._safe_path_fragment(access_code)
        destination.mkdir(parents=True, exist_ok=True)

        preserved_files: list[str] = []
        for candidate in sorted(temp_dir.iterdir()):
            if not candidate.is_file():
                continue
            target_path = destination / candidate.name
            shutil.copy2(candidate, target_path)
            preserved_files.append(str(target_path))
        return preserved_files

    def _safe_path_fragment(self, value: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
        return sanitized or "mopac_job"
