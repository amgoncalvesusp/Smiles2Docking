"""sPhysNet-Taut tautomer ranking backend (optional, not bundled).

sPhysNet-Taut (https://github.com/xiaolinpan/sPhysNet-Taut) ranks aqueous
tautomer ratios with a Siamese neural network. It depends on the compiled
PyTorch-Geometric extension stack (torch-scatter/sparse/cluster) and ships no
explicit licence, so it is intentionally NOT bundled with the frozen desktop
builds. When the optional dependency is present this backend enumerates
tautomers with RDKit and returns the sPhysNet-Taut top-ranked (dominant) one;
otherwise it raises a clear, actionable error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.tautomer.base import TautomerError
from src.tautomer.rdkit_adapter import enumerate_tautomers

_INSTALL_HINT = (
    "sPhysNet-Taut is an optional extra and is not bundled. Install it from "
    "https://github.com/xiaolinpan/sPhysNet-Taut (with torch, torch-geometric "
    "and torch-scatter/sparse/cluster), or set tautomer.backend to 'rdkit' / "
    "disable the tautomer step."
)


def _load_ranker() -> Callable[[list[str]], str]:
    """Return a callable ranking tautomer SMILES, or raise if unavailable.

    The sPhysNet-Taut project is distributed as a source repository rather than
    a stable importable API. We probe for a ``sphysnet_taut`` module exposing a
    ``rank_tautomers(smiles_list) -> best_smiles`` entry point; integrators can
    provide a thin shim of that shape.
    """
    try:
        import sphysnet_taut  # type: ignore
    except ImportError as exc:
        raise TautomerError(_INSTALL_HINT) from exc

    ranker = getattr(sphysnet_taut, "rank_tautomers", None)
    if not callable(ranker):
        raise TautomerError(
            "The installed sphysnet_taut module does not expose "
            "rank_tautomers(smiles_list). " + _INSTALL_HINT
        )
    return ranker


@dataclass(slots=True)
class SPhysNetTautomerizer:
    """Enumerate tautomers with RDKit, rank with sPhysNet-Taut."""

    settings: dict[str, Any]
    backend_name: str = field(default="sphysnet", init=False)

    def dominant_tautomer(self, smiles: str, access_code: str) -> str:
        max_tautomers = int(self.settings.get("max_tautomers", 16))
        candidates = enumerate_tautomers(smiles, access_code, max_tautomers)
        if len(candidates) == 1:
            return candidates[0]
        ranker = _load_ranker()
        try:
            best = ranker(candidates)
        except Exception as exc:  # pragma: no cover - optional dependency
            raise TautomerError(
                f"sPhysNet-Taut failed to rank tautomers for {access_code!r}: {exc}"
            ) from exc
        return best
