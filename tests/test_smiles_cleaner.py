import pytest

from src.preprocessing.smiles_cleaner import AmbiguousFragmentError, SmilesCleaner
from src.utils.models import MolecularRecord


def _record(smiles: str, access_code: str = "CMPD") -> MolecularRecord:
    return MolecularRecord(access_code=access_code, smiles=smiles, source_row=2)


def test_removes_counterion_and_keeps_parent_fragment() -> None:
    cleaner = SmilesCleaner({"preserve_kekule": True, "strict_fragment_disambiguation": True})
    result = cleaner.clean_record(_record("CC[NH+](C)C.[Cl-]"))

    assert result.salts_removed is True
    assert "Cl" not in result.cleaned_smiles


def test_raises_on_ambiguous_principal_fragment() -> None:
    cleaner = SmilesCleaner({"preserve_kekule": True, "strict_fragment_disambiguation": True})

    with pytest.raises(AmbiguousFragmentError):
        cleaner.clean_record(_record("CCO.CCN"))


def test_duplicate_principal_fragment_with_counterion_is_not_treated_as_ambiguous() -> None:
    cleaner = SmilesCleaner({"preserve_kekule": True, "strict_fragment_disambiguation": True})

    result = cleaner.clean_record(_record("CC(=O)[O-].CC(=O)[O-].[Ca+2]", access_code="EOS102210"))

    assert result.salts_removed is True
    assert result.cleaned_smiles == "CC(=O)[O-]"
