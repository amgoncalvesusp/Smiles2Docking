from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.protonation.base import ProtonationError, Protonator
from src.protonation.dimorphite_adapter import DimorphiteProtonator
from src.protonation.openbabel_adapter import OpenBabelError, OpenBabelProtonator


@dataclass(slots=True)
class NullProtonator:
    """Pass-through backend used when protonation is disabled."""

    settings: dict[str, Any]
    backend_name: str = field(default="none", init=False)

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        return smiles


def build_protonator(settings: dict[str, Any]) -> Protonator:
    backend = str(settings.get("backend", "molgpka")).strip().lower()
    if not settings.get("enabled", True):
        return NullProtonator(settings)
    if backend in {"molgpka", "gpka"}:
        # Imported lazily: MolGpKa pulls in torch, which is only needed when
        # this backend is actually selected.
        from src.protonation.molgpka_adapter import MolGpKaProtonator

        return MolGpKaProtonator(settings)
    if backend in {"dimorphite", "dimorphite_dl", "dimorphite-dl"}:
        return DimorphiteProtonator(settings)
    if backend in {"dimorphite_pick", "dimorphite-pick"}:
        # Legacy v1.x behaviour: Dimorphite-DL enumerates then a single state
        # is picked. Kept for reproducibility of pre-1.3 runs.
        return DimorphiteProtonator({**settings, "enumerate": False})
    if backend in {"openbabel", "obabel", "ob"}:
        return OpenBabelProtonator(settings)
    if backend in {"none", "off"}:
        return NullProtonator(settings)
    raise ProtonationError(
        f"Unknown protonation backend '{backend}'. "
        "Supported backends: molgpka, dimorphite, dimorphite_pick, openbabel, none."
    )


__all__ = [
    "NullProtonator",
    "ProtonationError",
    "OpenBabelError",
    "build_protonator",
]
