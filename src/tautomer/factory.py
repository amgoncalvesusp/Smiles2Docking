from __future__ import annotations

from typing import Any

from src.tautomer.base import TautomerError, Tautomerizer


def build_tautomerizer(settings: dict[str, Any] | None) -> Tautomerizer | None:
    """Return a tautomer backend, or ``None`` when the step is disabled.

    The tautomer step is opt-in (``tautomer.enabled: false`` by default). When
    enabled, ``rdkit`` uses RDKit's canonical tautomer; ``sphysnet`` ranks with
    the optional (unbundled) sPhysNet-Taut model.
    """
    settings = settings or {}
    if not settings.get("enabled", False):
        return None

    backend = str(settings.get("backend", "sphysnet")).strip().lower()
    if backend in {"rdkit", "canonical"}:
        from src.tautomer.rdkit_adapter import RDKitTautomerizer

        return RDKitTautomerizer(settings)
    if backend in {"sphysnet", "sphysnet-taut", "sphysnet_taut"}:
        from src.tautomer.sphysnet_adapter import SPhysNetTautomerizer

        return SPhysNetTautomerizer(settings)
    raise TautomerError(
        f"Unknown tautomer backend '{backend}'. Supported: rdkit, sphysnet."
    )
