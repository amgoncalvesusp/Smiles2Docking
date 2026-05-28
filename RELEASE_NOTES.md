# SMILES2Docking v1.2 — Additive reviewer-driven features

**Date:** 2026-05-28
**License:** GPL-2.0-or-later
**Repository:** https://github.com/amgoncalvesusp/Smiles2Docking

## Summary

Version 1.2 builds **directly on the canonical 1.1.1 base** and adds new
capabilities **without removing any 1.1.1 functionality**. The full 1.1.1
GUI is preserved — including the MOPAC PM7 toggle and the stereochemistry
controls — and is extended with a protonation-backend selector. Under the
hood, protonation gains a SMARTS-based multi-site backend (Dimorphite-DL),
PDBQT export is rebuilt on Meeko to fix molecule fragmentation, and the
JSON RunReport now records per-molecule timing.

## Highlights

- **Protonation backend selector in the GUI.** Choose
  Dimorphite-DL / Open Babel / None directly from the processing options.
  Dimorphite-DL is SMARTS-based, substituent-aware, and multi-site;
  Open Babel remains available as the legacy backend.
- **Dimorphite-DL adapter is version-robust.** Supports both the v2.x
  module-level `protonate_smiles()` API and the v1.x `DimorphiteDL` class.
- **PDBQT export rebuilt on Meeko.** Solves molecule fragmentation in
  AutoDock Vina pipelines (replaces the Open Babel `-xh` path).
- **MOPAC PM7 refinement and stereochemistry controls retained** from
  1.1.1 — no GUI capability was lost.
- **Per-molecule timing in the JSON RunReport.** `started_at`,
  `finished_at`, `wall_clock_seconds`, per-record seconds, mean/median/p95,
  fastest/slowest, throughput (molecules/min).
- **AppImage / frozen read-only failure fixed.** XDG/APPDATA user-writable
  output paths via `src/utils/app_paths.py`. No more
  `[Errno 30] Read-only file system` on AppImage launches.

## Configuration changes

`config/settings.yaml` `protonation` block:

```yaml
protonation:
  backend: dimorphite          # dimorphite | openbabel | none
  enabled: true
  ph: 7.4
  ph_tolerance: 1.0
  max_variants: 1
  variant_selection: first     # first | most_neutral
  pka_precision: 1.0
```

`export` block adds a `pdbqt` section:

```yaml
export:
  pdbqt:
    rigid: false
    add_hydrogens: true
    keep_nonpolar_hydrogens: false
    charge_model: gasteiger
```

The 1.1.1 `pm7` block and processing stereochemistry keys are unchanged.

## New / pinned dependencies

| Package | Min version | Purpose |
|---------|-------------|---------|
| `dimorphite-dl` | 1.3 | Multi-site protonation backend |
| `meeko` | 0.5 | PDBQT writer |
| `scipy` | 1.10 | Meeko transitive dep (geometry) |
| `gemmi` | 0.6 | Meeko transitive dep (structure I/O) |

`python-docx` is required only by the manuscript builders under `Artigo/`.

## RunReport schema additions

```json
{
  "protonation_backend": "dimorphite",
  "started_at": "2026-05-28T12:34:56+00:00",
  "finished_at": "2026-05-28T12:35:09+00:00",
  "wall_clock_seconds": 12.45,
  "mean_seconds_per_record": 0.124,
  "median_seconds_per_record": 0.110,
  "p95_seconds_per_record": 0.231,
  "fastest_seconds": 0.043,
  "slowest_seconds": 0.412,
  "throughput_molecules_per_minute": 481.9,
  "per_record_timings": [
    { "access_code": "LIG_001", "seconds": 0.124 }
  ]
}
```

## Test status

```
49 passed, 3 skipped
```

End-to-end smoke check: Dimorphite-DL protonates aspirin to
`CC(=O)Oc1ccccc1C(=O)[O-]`; Meeko writes a single connected PDBQT ROOT
block per molecule.

## Upgrade notes

- Existing 1.1.x `settings.yaml` files continue to work. To keep the
  legacy protonation behaviour, set `protonation.backend: openbabel`.
- `protonation.temp_dir` and `export.output_dir` may be left empty; the
  resolver places outputs under the user-writable XDG/APPDATA path.

## Acknowledgements

Reviewers of *Molecular Informatics* for the critique that motivated the
protonation and PDBQT-export improvements.
