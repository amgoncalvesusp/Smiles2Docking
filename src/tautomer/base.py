from __future__ import annotations

from typing import Protocol


class TautomerError(Exception):
    """Raised when tautomer selection fails."""


class Tautomerizer(Protocol):
    backend_name: str

    def dominant_tautomer(self, smiles: str, access_code: str) -> str: ...
