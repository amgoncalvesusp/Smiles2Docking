from __future__ import annotations

import pytest
from rdkit import Chem

from src.validation.structure_validator import StructureValidationError, StructureValidator


def _formal_charge(molecule: Chem.Mol) -> int:
    return sum(atom.GetFormalCharge() for atom in molecule.GetAtoms())


def test_stereochemistry_enumeration_expands_single_undefined_center() -> None:
    validator = StructureValidator({"strict_stereochemistry": True})

    variants = validator.enumerate_input_variants("CC(F)Cl", "CHIRAL")

    assert len(variants) == 2
    assert {variant.access_code for variant in variants} == {
        "CHIRAL__atom2_clockwise",
        "CHIRAL__atom2_anticlockwise",
    }
    assert {variant.smiles for variant in variants} == {"C[C@H](F)Cl", "C[C@@H](F)Cl"}


def test_stereochemistry_enumeration_expands_two_undefined_centers() -> None:
    validator = StructureValidator({"strict_stereochemistry": True})

    variants = validator.enumerate_input_variants("CC(F)C(Cl)Br", "DI_CHIRAL")

    assert len(variants) == 4
    assert {variant.access_code for variant in variants} == {
        "DI_CHIRAL__atom2_clockwise__atom4_clockwise",
        "DI_CHIRAL__atom2_clockwise__atom4_anticlockwise",
        "DI_CHIRAL__atom2_anticlockwise__atom4_clockwise",
        "DI_CHIRAL__atom2_anticlockwise__atom4_anticlockwise",
    }


def test_stereochemistry_enumeration_respects_variant_cap() -> None:
    validator = StructureValidator(
        {"strict_stereochemistry": True, "max_stereochemistry_variants": 8}
    )

    resolution = validator.resolve_input_variants("CC(F)C(Cl)C(Br)C(I)N", "TOO_MANY_VARIANTS")

    assert resolution.variants == []
    assert resolution.action == "skipped_variant_limit"
    assert "more than 8 variants" in str(resolution.reason)


def test_single_undefined_center_policy_accepts_exactly_one_undefined_center() -> None:
    validator = StructureValidator(
        {"strict_stereochemistry": True, "single_undefined_stereocenter_only": True}
    )

    resolution = validator.resolve_input_variants("CC(F)Cl", "ONE_CENTER")

    assert len(resolution.variants) == 2
    assert resolution.undefined_center_count == 1
    assert resolution.action == "enumerated_single_undefined_center"


def test_single_undefined_center_policy_skips_multiple_undefined_centers() -> None:
    validator = StructureValidator(
        {"strict_stereochemistry": True, "single_undefined_stereocenter_only": True}
    )

    resolution = validator.resolve_input_variants("CC(F)C(Cl)Br", "TWO_CENTERS")

    assert resolution.variants == []
    assert resolution.undefined_center_count == 2
    assert resolution.action == "skipped_multiple_undefined_centers"
    assert "exactly one undefined center" in str(resolution.reason)


def test_skip_undefined_stereo_detects_undefined_non_nitrogen_center() -> None:
    validator = StructureValidator({"skip_undefined_stereo": True})

    analysis = validator.analyze_undefined_stereochemistry("CC(F)Cl", "CHIRAL")

    assert analysis.should_skip is True
    assert analysis.undefined_center_count == 1


def test_skip_undefined_stereo_detects_tertiary_amine_that_becomes_chiral_after_protonation() -> None:
    validator = StructureValidator({"skip_undefined_stereo": True})

    analysis = validator.analyze_undefined_stereochemistry("CCN(C)CCC", "TERTIARY_AMINE")

    assert analysis.should_skip is True
    assert analysis.undefined_center_count == 1


def test_skip_undefined_stereo_ignores_unprotonated_nitrogen_without_post_protonation_chirality() -> None:
    validator = StructureValidator({"skip_undefined_stereo": True})

    analysis = validator.analyze_undefined_stereochemistry("CN(C)CC", "ACHIRAL_TERTIARY_AMINE")

    assert analysis.should_skip is False
    assert analysis.undefined_center_count == 0


def test_protonated_smiles_validation_does_not_apply_strict_stereochemistry() -> None:
    validator = StructureValidator({"strict_stereochemistry": True})

    protonated = validator.validate_protonated_smiles("CC(F)Cl", "CHIRAL")

    assert protonated == "CC(F)Cl"


def test_input_validation_accepts_smiles_with_and_without_explicit_hydrogens() -> None:
    validator = StructureValidator({"strict_stereochemistry": True})

    implicit = validator.validate_input_smiles("CCO", "ETHANOL_IMPLICIT_H")
    explicit = validator.validate_input_smiles("[H]OC([H])([H])C([H])([H])[H]", "ETHANOL_EXPLICIT_H")

    implicit_molecule = Chem.MolFromSmiles(implicit)
    explicit_molecule = Chem.MolFromSmiles(explicit)
    assert implicit_molecule is not None
    assert explicit_molecule is not None
    assert _formal_charge(implicit_molecule) == 0
    assert _formal_charge(explicit_molecule) == 0


def test_stereochemistry_enumeration_handles_explicit_hydrogens() -> None:
    validator = StructureValidator({"strict_stereochemistry": True})

    variants = validator.enumerate_input_variants("[H]C([H])([H])C([H])(F)Cl", "CHIRAL_EXPLICIT_H")

    assert len(variants) == 2
    assert {variant.access_code for variant in variants} == {
        "CHIRAL_EXPLICIT_H__atom2_clockwise",
        "CHIRAL_EXPLICIT_H__atom2_anticlockwise",
    }


def test_post_pm7_validation_can_rescue_obvious_charge_loss() -> None:
    validator = StructureValidator({"allow_post_mopac_charge_rescue": True})
    molecule = Chem.AddHs(Chem.MolFromSmiles("C[N+](C)(C)C"))
    assert molecule is not None

    nitrogen = next(atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 7)
    nitrogen.SetFormalCharge(0)

    validated = validator.validate_final_molecule(molecule, "TETRAMETHYLAMMONIUM", "post_pm7", expected_charge=1)

    assert _formal_charge(validated) == 1
    assert validated.GetProp("validation_status") == "rescued"
    assert validated.GetProp("validation_rescue") == "formal_charge_normalization"


def test_post_pm7_validation_fails_without_rescue_when_disabled() -> None:
    validator = StructureValidator({"allow_post_mopac_charge_rescue": False})
    molecule = Chem.AddHs(Chem.MolFromSmiles("C[N+](C)(C)C"))
    assert molecule is not None

    nitrogen = next(atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 7)
    nitrogen.SetFormalCharge(0)

    with pytest.raises(StructureValidationError, match="Structure validation failed"):
        validator.validate_final_molecule(molecule, "TETRAMETHYLAMMONIUM", "post_pm7", expected_charge=1)
