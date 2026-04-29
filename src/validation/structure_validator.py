from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rdkit import Chem
from rdkit.Chem.EnumerateStereoisomers import EnumerateStereoisomers, StereoEnumerationOptions

from src.utils.models import (
    StereochemistryResolution,
    StereochemistryVariant,
    UndefinedStereoAnalysis,
)


class StructureValidationError(Exception):
    """Raised when a protonated or optimized structure fails validation."""


@dataclass(slots=True)
class StructureValidator:
    settings: dict[str, Any]

    def describe_stereochemistry_policy(self) -> str:
        if self.settings.get("single_undefined_stereocenter_only", False):
            return "single_undefined_only"
        if self.settings.get("strict_stereochemistry", False):
            return "enumerate_all_with_cap"
        return "disabled"

    def resolve_input_variants(self, smiles: str, access_code: str) -> StereochemistryResolution:
        molecule = self._parse_smiles(smiles, access_code, context="input")
        canonical_smiles = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
        base_variant = StereochemistryVariant(
            access_code=access_code,
            smiles=canonical_smiles,
            source_access_code=access_code,
        )
        policy = self.describe_stereochemistry_policy()
        if policy == "disabled":
            return StereochemistryResolution(variants=[base_variant])

        atom_centers = self._unassigned_atom_centers(molecule)
        if not atom_centers:
            return StereochemistryResolution(variants=[base_variant])

        if policy == "single_undefined_only" and len(atom_centers) != 1:
            return StereochemistryResolution(
                variants=[],
                undefined_center_count=len(atom_centers),
                action="skipped_multiple_undefined_centers",
                reason=(
                    f"Found {len(atom_centers)} undefined tetrahedral stereocenters for {access_code!r}. "
                    f"The current policy accepts only molecules with exactly one undefined center."
                ),
            )

        max_variants = max(1, int(self.settings.get("max_stereochemistry_variants", 16)))
        options = StereoEnumerationOptions(
            tryEmbedding=False,
            unique=True,
            onlyUnassigned=True,
            maxIsomers=max_variants + 1,
        )
        variants: list[StereochemistryVariant] = []
        for enumerated in EnumerateStereoisomers(molecule, options=options):
            Chem.AssignStereochemistry(enumerated, force=True, cleanIt=True)
            descriptors = self._atom_stereo_descriptors(enumerated, atom_centers)
            suffix = "__".join(descriptors)
            variant_code = f"{access_code}__{suffix}" if suffix else access_code
            variants.append(
                StereochemistryVariant(
                    access_code=variant_code,
                    smiles=Chem.MolToSmiles(enumerated, canonical=True, isomericSmiles=True),
                    descriptors=descriptors,
                    source_access_code=access_code,
                )
            )

        if not variants:
            raise StructureValidationError(f"Unable to enumerate stereochemistry variants for {access_code!r}")
        if len(variants) > max_variants:
            return StereochemistryResolution(
                variants=[],
                undefined_center_count=len(atom_centers),
                action="skipped_variant_limit",
                reason=(
                    f"Enumerating unresolved stereochemistry for {access_code!r} would generate more than "
                    f"{max_variants} variants. Define stereochemistry explicitly or raise "
                    f"processing.max_stereochemistry_variants."
                ),
            )

        action = "enumerated_single_undefined_center" if len(atom_centers) == 1 else "enumerated_multiple_undefined_centers"
        reason = (
            "Exactly one undefined tetrahedral stereocenter was expanded into explicit stereoisomers."
            if len(atom_centers) == 1
            else f"{len(atom_centers)} undefined tetrahedral stereocenters were expanded into explicit stereoisomers."
        )
        return StereochemistryResolution(
            variants=variants,
            undefined_center_count=len(atom_centers),
            action=action,
            reason=reason,
        )

    def enumerate_input_variants(self, smiles: str, access_code: str) -> list[StereochemistryVariant]:
        resolution = self.resolve_input_variants(smiles, access_code)
        if not resolution.variants:
            raise StructureValidationError(
                resolution.reason or f"Unable to enumerate stereochemistry variants for {access_code!r}"
            )
        return resolution.variants

    def analyze_undefined_stereochemistry(self, smiles: str, access_code: str) -> UndefinedStereoAnalysis:
        molecule = self._parse_smiles(smiles, access_code, context="input")
        undefined_atom_centers = self._unassigned_non_nitrogen_atom_centers(molecule)
        protonated_nitrogens = self._undefined_nitrogen_centers_after_protonation(molecule)
        undefined_center_count = len(undefined_atom_centers) + len(protonated_nitrogens)
        return UndefinedStereoAnalysis(
            should_skip=bool(self.settings.get("skip_undefined_stereo", False) and undefined_center_count > 0),
            undefined_center_count=undefined_center_count,
        )

    def validate_input_smiles(self, smiles: str, access_code: str) -> str:
        molecule = self._parse_smiles(smiles, access_code, context="input")
        return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)

    def validate_protonated_smiles(self, smiles: str, access_code: str) -> str:
        molecule = self._parse_smiles(smiles, access_code, context="protonated")
        return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)

    def formal_charge_from_smiles(self, smiles: str, access_code: str) -> int:
        molecule = self._parse_smiles(smiles, access_code, context="protonated")
        return self._formal_charge(molecule)

    def _parse_smiles(self, smiles: str, access_code: str, context: str) -> Chem.Mol:
        molecule = Chem.MolFromSmiles(smiles, sanitize=True)
        if molecule is None:
            raise StructureValidationError(f"Unable to parse {context} SMILES for {access_code!r}")
        return molecule

    def validate_final_molecule(
        self,
        molecule: Chem.Mol,
        access_code: str,
        stage: str,
        expected_charge: int | None = None,
    ) -> Chem.Mol:
        working_copy = Chem.Mol(molecule)
        validation_status = "validated"

        try:
            Chem.SanitizeMol(working_copy)
        except Exception as exc:
            rescued = self._rescue_post_mopac_structure(working_copy)
            if stage != "post_pm7" or rescued is None:
                raise StructureValidationError(
                    f"Structure validation failed for {access_code!r} after {stage}: {exc}"
                ) from exc
            working_copy = rescued
            validation_status = "rescued"

        actual_charge = self._formal_charge(working_copy)
        if expected_charge is not None and actual_charge != expected_charge:
            raise StructureValidationError(
                f"Net charge changed for {access_code!r} after {stage}: expected {expected_charge}, found {actual_charge}"
            )

        working_copy.SetProp("validation_stage", stage)
        working_copy.SetProp("validation_status", validation_status)
        working_copy.SetProp("validated_net_charge", str(actual_charge))
        if validation_status == "rescued":
            working_copy.SetProp("validation_rescue", "formal_charge_normalization")
        return working_copy

    def _rescue_post_mopac_structure(self, molecule: Chem.Mol) -> Chem.Mol | None:
        if not self.settings.get("allow_post_mopac_charge_rescue", True):
            return None

        rescued = Chem.Mol(molecule)
        changed = False
        for atom in rescued.GetAtoms():
            explicit_valence = int(atom.GetExplicitValence())
            if atom.GetAtomicNum() == 7 and atom.GetFormalCharge() == 0 and explicit_valence == 4:
                atom.SetFormalCharge(1)
                changed = True
            elif atom.GetAtomicNum() == 8 and atom.GetFormalCharge() == 0 and explicit_valence == 1:
                atom.SetFormalCharge(-1)
                changed = True

        if not changed:
            return None

        for atom in rescued.GetAtoms():
            atom.UpdatePropertyCache(strict=False)

        try:
            Chem.SanitizeMol(rescued)
            return rescued
        except Exception:
            pass

        non_kekulized = Chem.Mol(rescued)
        for atom in non_kekulized.GetAtoms():
            atom.SetIsAromatic(False)
            atom.UpdatePropertyCache(strict=False)
        for bond in non_kekulized.GetBonds():
            bond.SetIsAromatic(False)

        try:
            Chem.SanitizeMol(non_kekulized, sanitizeOps=Chem.SANITIZE_ALL ^ Chem.SANITIZE_KEKULIZE)
        except Exception:
            return None
        return non_kekulized

    def _formal_charge(self, molecule: Chem.Mol) -> int:
        return int(sum(atom.GetFormalCharge() for atom in molecule.GetAtoms()))

    def _unassigned_non_nitrogen_atom_centers(self, molecule: Chem.Mol) -> list[int]:
        return [
            atom_idx
            for atom_idx in self._unassigned_atom_centers(molecule)
            if molecule.GetAtomWithIdx(atom_idx).GetAtomicNum() != 7
        ]

    def _undefined_nitrogen_centers_after_protonation(self, molecule: Chem.Mol) -> list[int]:
        return [
            atom.GetIdx()
            for atom in molecule.GetAtoms()
            if self._becomes_undefined_chiral_nitrogen_after_protonation(molecule, atom.GetIdx())
        ]

    def _becomes_undefined_chiral_nitrogen_after_protonation(self, molecule: Chem.Mol, atom_idx: int) -> bool:
        atom = molecule.GetAtomWithIdx(atom_idx)
        if atom.GetAtomicNum() != 7:
            return False
        if atom.GetFormalCharge() != 0 or atom.GetDegree() != 3 or atom.GetTotalNumHs() != 0:
            return False
        if atom.GetIsAromatic():
            return False
        if atom.GetHybridization() not in {
            Chem.rdchem.HybridizationType.SP3,
            Chem.rdchem.HybridizationType.UNSPECIFIED,
        }:
            return False

        protonated = Chem.RWMol(Chem.Mol(molecule))
        hydrogen = Chem.Atom(1)
        hydrogen.SetNoImplicit(True)
        hydrogen_idx = protonated.AddAtom(hydrogen)
        protonated.AddBond(atom_idx, hydrogen_idx, Chem.BondType.SINGLE)
        protonated_atom = protonated.GetAtomWithIdx(atom_idx)
        protonated_atom.SetFormalCharge(1)
        protonated_atom.SetNoImplicit(True)

        protonated_molecule = protonated.GetMol()
        try:
            Chem.SanitizeMol(protonated_molecule)
        except Exception:
            return False

        Chem.AssignStereochemistry(protonated_molecule, force=True, cleanIt=True)
        return any(
            center_idx == atom_idx and label == "?"
            for center_idx, label in Chem.FindMolChiralCenters(
                protonated_molecule,
                includeUnassigned=True,
                useLegacyImplementation=False,
            )
        )

    def _unassigned_atom_centers(self, molecule: Chem.Mol) -> list[int]:
        probe = Chem.Mol(molecule)
        try:
            probe = Chem.RemoveHs(probe)
        except Exception:
            pass
        Chem.AssignStereochemistry(probe, force=True, cleanIt=True)
        return sorted(
            center_idx
            for center_idx, label in Chem.FindMolChiralCenters(
                probe,
                includeUnassigned=True,
                useLegacyImplementation=False,
            )
            if label == "?"
        )

    def _atom_stereo_descriptors(self, molecule: Chem.Mol, atom_indices: list[int]) -> list[str]:
        descriptors: list[str] = []
        for atom_idx in atom_indices:
            atom = molecule.GetAtomWithIdx(atom_idx)
            tag = atom.GetChiralTag()
            if tag == Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CW:
                orientation = "clockwise"
            elif tag == Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CCW:
                orientation = "anticlockwise"
            else:
                orientation = "unspecified"
            descriptors.append(f"atom{atom_idx + 1}_{orientation}")
        return descriptors
