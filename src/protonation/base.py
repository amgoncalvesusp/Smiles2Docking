from __future__ import annotations

from typing import Protocol, runtime_checkable


class ProtonationError(Exception):
    """Raised when a protonation backend fails."""


class Protonator(Protocol):
    backend_name: str

    def protonate_smiles(self, smiles: str, access_code: str) -> str: ...


@runtime_checkable
class MultiStateProtonator(Protocol):
    """Backends that can return several plausible protonation states.

    Single-state backends only implement ``protonate_smiles``; enumeration
    backends (e.g. Dimorphite-DL) additionally implement ``protonate_states``.
    """

    backend_name: str

    def protonate_states(self, smiles: str, access_code: str) -> list[str]: ...


def iter_protonation_states(
    protonator: object, smiles: str, access_code: str
) -> list[str]:
    """Return every protonation state a backend produces for one SMILES.

    Uses ``protonate_states`` when the backend provides it, otherwise falls
    back to the single state from ``protonate_smiles``. Always returns at least
    one SMILES so downstream fan-out is uniform.
    """
    states_method = getattr(protonator, "protonate_states", None)
    if callable(states_method):
        states = list(states_method(smiles, access_code))
        return states if states else [smiles]
    return [protonator.protonate_smiles(smiles, access_code)]
