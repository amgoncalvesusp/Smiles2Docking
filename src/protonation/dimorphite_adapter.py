from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rdkit import Chem

from src.protonation.base import ProtonationError


@dataclass(slots=True)
class DimorphiteProtonator:
    """Protonation backend using Dimorphite-DL.

    Dimorphite-DL applies SMARTS-based pKa rules that account for
    multiple ionizable centers and substituent effects, addressing
    limitations of the Open Babel `-p` mode that protonates every
    ionizable group independently.
    """

    settings: dict[str, Any]
    backend_name: str = field(default="dimorphite", init=False)
    _ruleset_verified: bool = field(default=False, init=False)

    def _enumerate(self, smiles: str, access_code: str, max_variants: int) -> list[str]:
        """Return the unique protonation states Dimorphite-DL predicts."""
        try:
            import dimorphite_dl as _dd
        except ImportError as exc:
            raise ProtonationError(
                "dimorphite_dl is not installed. Install it via `pip install dimorphite-dl` "
                "or switch the protonation backend to 'openbabel' in settings."
            ) from exc

        if not self._ruleset_verified:
            self._verify_ruleset_loaded()
            self._ruleset_verified = True

        ph = float(self.settings.get("ph", 7.4))
        ph_tol = float(self.settings.get("ph_tolerance", 1.0))
        pka_precision = float(self.settings.get("pka_precision", 1.0))

        try:
            variants = self._run_dimorphite(
                _dd, smiles, ph, ph_tol, max_variants, pka_precision
            )
        except ProtonationError:
            raise
        except Exception as exc:
            raise ProtonationError(
                f"Dimorphite-DL failed to protonate {access_code!r}: {exc}"
            ) from exc

        if not variants:
            raise ProtonationError(
                f"Dimorphite-DL returned no variants for {access_code!r}"
            )
        # De-duplicate while preserving Dimorphite's ordering.
        return list(dict.fromkeys(variants))

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        """Single dominant-ish state (legacy 'dimorphite_pick' behaviour).

        Dimorphite-DL does not rank a physically dominant microstate, so this
        merely picks one of its enumerated states. The default backend is
        MolGpKa; use :meth:`protonate_states` to expose all states instead.
        """
        if not self.settings.get("enabled", True):
            return smiles

        max_variants = int(self.settings.get("max_variants", 1))
        variants = self._enumerate(smiles, access_code, max_variants)
        keep_label = str(self.settings.get("variant_selection", "first")).lower()
        if keep_label == "most_neutral":
            return min(variants, key=lambda smi: _abs_formal_charge(smi, access_code))
        return variants[0]

    def protonate_states(self, smiles: str, access_code: str) -> list[str]:
        """All plausible protonation states in the configured pH window.

        This is the enumeration mode requested in review: rather than silently
        returning one arbitrary state, every state Dimorphite-DL predicts is
        handed back to the caller. Set ``enumerate: false`` to fall back to the
        single-state ``protonate_smiles`` behaviour.
        """
        if not self.settings.get("enabled", True):
            return [smiles]
        if not self.settings.get("enumerate", True):
            return [self.protonate_smiles(smiles, access_code)]
        max_variants = int(self.settings.get("max_variants", 128))
        return self._enumerate(smiles, access_code, max_variants)

    @staticmethod
    def _verify_ruleset_loaded() -> None:
        """Fail loudly if Dimorphite-DL cannot load its SMARTS ruleset.

        Dimorphite-DL's ``PKaData`` is a singleton that assigns its instance
        *before* loading the SMARTS data file. If that first load fails (e.g. a
        frozen build that did not bundle ``dimorphite_dl.smarts``), the singleton
        is left with an empty ruleset and every subsequent molecule is returned
        unprotonated with no error. Force the one-time load here and abort the
        run rather than emit silently wrong chemistry.
        """
        try:
            from dimorphite_dl.protonate.data import PKaData
        except Exception:
            # Unknown dimorphite_dl layout: fall back to the per-molecule error
            # path instead of guessing at internals.
            return

        try:
            PKaData()
        except Exception as exc:
            raise ProtonationError(
                f"Dimorphite-DL could not load its SMARTS ruleset: {exc}. "
                "Aborting to avoid silently producing unprotonated structures."
            ) from exc

        if not getattr(PKaData, "_data", None):
            raise ProtonationError(
                "Dimorphite-DL loaded an empty SMARTS ruleset; aborting to avoid "
                "silently producing unprotonated structures."
            )

    @staticmethod
    def _run_dimorphite(
        module: Any,
        smiles: str,
        ph: float,
        ph_tol: float,
        max_variants: int,
        pka_precision: float,
    ) -> list[str]:
        """Run Dimorphite-DL across both the v2 (function) and v1 (class) APIs."""
        ph_min = ph - ph_tol
        ph_max = ph + ph_tol

        # Dimorphite-DL v2.x: module-level protonate_smiles() returning list[str]
        func = getattr(module, "protonate_smiles", None)
        if callable(func):
            result = func(
                smiles,
                ph_min=ph_min,
                ph_max=ph_max,
                precision=pka_precision,
                max_variants=max_variants,
                label_states=False,
            )
            return list(result)

        # Dimorphite-DL v1.x: DimorphiteDL class with .protonate()
        engine_cls = getattr(module, "DimorphiteDL", None)
        if engine_cls is not None:
            engine = engine_cls(
                min_ph=ph_min,
                max_ph=ph_max,
                max_variants=max_variants,
                label_states=False,
                pka_precision=pka_precision,
            )
            return list(engine.protonate(smiles))

        raise ProtonationError(
            "Unsupported dimorphite_dl version: neither protonate_smiles() nor "
            "DimorphiteDL is available."
        )


def _abs_formal_charge(smiles: str, access_code: str) -> int:
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ProtonationError(f"Invalid SMILES emitted for {access_code!r}: {smiles}")
    return abs(Chem.GetFormalCharge(molecule))
