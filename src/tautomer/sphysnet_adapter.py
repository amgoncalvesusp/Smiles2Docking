"""sPhysNet-Taut tautomer + protonation backend (external, subprocess, not bundled).

sPhysNet-Taut (https://github.com/xiaolinpan/sPhysNet-Taut) enumerates tautomers
and ranks them by predicted aqueous free energy. It depends on the compiled
PyTorch-Geometric extension stack and ships no explicit licence, so it is not
bundled with the desktop builds; the user installs it in a dedicated conda
environment (see the README) and points SMILES2Docking at its
``predict_tautomer.py`` script.

The script is invoked as a subprocess. With ``--ionization 1 --ph P`` it returns
the lowest-energy tautomer already protonated at the requested pH, so its output
requires no further protonation step (``produces_protonated`` is True and the
pipeline exports the returned SMILES directly).

Expected stdout is a Python-literal list of records ordered by energy, e.g.::

    [{'tsmi': '...', 'psmis': ['<protonated SMILES>'], 'score': '0.0',
      'label': 'low_energy'}, ...]

The first record is the dominant (lowest-energy) tautomer; its first protonated
SMILES is selected.
"""

from __future__ import annotations

import ast
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rdkit import Chem

from src.tautomer.base import TautomerError

_INSTALL_HINT = (
    "Install sPhysNet-Taut in a dedicated conda environment and set "
    "tautomer.sphysnet.script_path to its predict_tautomer.py:\n"
    "  git clone https://github.com/xiaolinpan/sPhysNet-Taut.git\n"
    "  conda env create -n tautomer_selection -f sPhysNet-Taut/environment.yaml\n"
    "  conda activate tautomer_selection\n"
    "  conda install treelib\n"
    "then set tautomer.sphysnet.python to that environment's python executable."
)

# predict_tautomer.py samples conformers and runs a network; allow a generous
# per-molecule ceiling so slow machines do not abort a valid run.
_SUBPROCESS_TIMEOUT_S = 900


@dataclass(slots=True)
class SPhysNetTautomerizer:
    """Select the dominant, protonated tautomer via an external sPhysNet-Taut run."""

    settings: dict[str, Any]
    backend_name: str = field(default="sphysnet", init=False)
    # Its output is already protonated at the requested pH; the pipeline must not
    # protonate it again.
    produces_protonated: bool = field(default=True, init=False)

    def dominant_tautomer(self, smiles: str, access_code: str) -> str:
        cfg = dict(self.settings.get("sphysnet", {}))
        script = str(cfg.get("script_path", "")).strip()
        if not script or not Path(script).is_file():
            raise TautomerError(
                f"sPhysNet-Taut script not found for {access_code!r}: {script!r}. "
                + _INSTALL_HINT
            )
        python_cmd = _resolve_python(cfg)
        num_confs = int(cfg.get("num_confs", 100))
        ph = float(self.settings.get("ph", 7.4))

        command = python_cmd + [
            script,
            "--smi",
            smiles,
            "--num_confs",
            str(num_confs),
            "--ionization",
            "1",
            "--ph",
            f"{ph}",
        ]
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=_SUBPROCESS_TIMEOUT_S,
                cwd=str(Path(script).resolve().parent),
            )
        except FileNotFoundError as exc:
            raise TautomerError(
                f"Could not launch the sPhysNet-Taut python for {access_code!r} "
                f"({exc}). " + _INSTALL_HINT
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise TautomerError(
                f"sPhysNet-Taut timed out for {access_code!r} after "
                f"{_SUBPROCESS_TIMEOUT_S}s."
            ) from exc

        if proc.returncode != 0:
            raise TautomerError(
                f"sPhysNet-Taut failed for {access_code!r} (exit {proc.returncode}): "
                f"{(proc.stderr or proc.stdout).strip()[:400]}"
            )
        return _parse_dominant(proc.stdout, smiles, access_code)


def _resolve_python(cfg: dict) -> list[str]:
    """Return the command prefix that runs python in the sPhysNet-Taut env."""
    python = str(cfg.get("python", "")).strip()
    if not python:
        return ["python"]
    # Allow either a bare executable path or a full command such as
    # "conda run -n tautomer_selection python".
    return shlex.split(python, posix=False) if (" " in python) else [python]


def _parse_dominant(stdout: str, smiles: str, access_code: str) -> str:
    """Extract the protonated dominant-tautomer SMILES from the script output."""
    records = None
    for line in reversed(stdout.splitlines()):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)
            except (ValueError, SyntaxError):
                continue
            if isinstance(parsed, list) and parsed:
                records = parsed
                break
    if not records:
        raise TautomerError(
            f"Could not parse sPhysNet-Taut output for {access_code!r}. "
            f"Output was: {stdout.strip()[:300]!r}"
        )

    dominant = records[0]
    psmis = dominant.get("psmis") if isinstance(dominant, dict) else None
    if isinstance(psmis, (list, tuple)):
        chosen = psmis[0] if psmis else None
    elif isinstance(psmis, str):
        chosen = psmis
    else:
        chosen = None
    if not chosen or Chem.MolFromSmiles(chosen) is None:
        raise TautomerError(
            f"sPhysNet-Taut returned an unusable SMILES for {access_code!r}: {chosen!r}"
        )
    return Chem.MolToSmiles(Chem.MolFromSmiles(chosen))
