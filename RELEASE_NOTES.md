# SMILES2Docking v0.3.0 — Reviewer-driven revisions

**Date:** 2026-05-27
**License:** GPL-2.0-or-later
**Repository:** https://github.com/amgoncalvesusp/Smiles2Docking

## Summary

Version 0.3.0 lands the full set of revisions requested by Reviewer #1 of
*Molecular Informatics*, together with one separately reported fix
(PDBQT fragmentation). The pipeline is repositioned as a curated,
auditable ligand-preparation tool for libraries of 10²–10⁴ compounds,
with explicit attention to protonation accuracy, parallel scalability,
PDBQT topology, and per-molecule performance reporting.

## Highlights

- **Dimorphite-DL is the new default protonation backend.** SMARTS-based,
  substituent-aware, multi-site. Open Babel remains available as a
  legacy backend (`protonation.backend: openbabel`).
- **PDBQT export rebuilt on Meeko.** Solves molecule fragmentation in
  AutoDock Vina pipelines. New modes: `separate_pdbqt`, `single_pdbqt`.
- **Parallel processing via joblib.** Configure via `parallel.n_jobs`;
  worker-isolated cleaner/protonator/builder.
- **MOPAC PM7 refinement is now opt-in.** Default off, fails soft, keeps
  force-field geometry on failure. PM6, PM6-D3H4X, PM6-ORG, RM1, PM3,
  AM1, MNDO available for method-comparison.
- **Per-molecule timing in the JSON RunReport.** Stage-resolved seconds
  (`clean`, `protonate`, `build_3d`, `export`), mean/median/p95,
  fastest/slowest, throughput (molecules/min), wall-clock,
  `started_at` / `finished_at`, `n_jobs_used`.
- **AppImage read-only failure fixed.** XDG/APPDATA user-writable
  output paths via `src/utils/app_paths.py`. No more
  `[Errno 30] Read-only file system` on AppImage launches.
- **Benchmark script.** `scripts/benchmark.py` reproduces throughput
  across library sizes and worker counts; output CSV is written under
  `data/reports/benchmark_<timestamp>.csv`.

## Configuration changes

`config/settings.yaml` adds:

```yaml
protonation:
  backend: dimorphite          # dimorphite | openbabel | none
  ph: 7.4
  ph_tolerance: 1.0
  max_variants: 1
  variant_selection: first
  pka_precision: 1.0

structure_generation:
  mopac:
    enabled: false             # opt-in
    method: PM7

parallel:
  enabled: true
  n_jobs: -1                   # -1 = all cores
  backend: loky
  batch_size: auto

export:
  output_dir: ""               # blank => user-writable XDG/APPDATA path
  temp_dir: ""
  mode: separate_mol2          # separate_mol2 | single_mol2 | separate_sdf | single_sdf | separate_pdbqt | single_pdbqt
  pdbqt:
    rigid: false
    add_hydrogens: true
    keep_nonpolar_hydrogens: false
    charge_model: gasteiger
```

## New dependencies

| Package | Min version | Purpose |
|---------|-------------|---------|
| `joblib` | 1.3 | Parallel worker pool |
| `dimorphite-dl` | 1.3 | Default protonation backend |
| `meeko` | 0.5 | PDBQT writer |

`python-docx` is required only by the article and response-letter
builders under `Artigo/`.

## RunReport schema additions

```json
{
  "wall_clock_seconds": 12.45,
  "mean_seconds_per_record": 0.124,
  "median_seconds_per_record": 0.110,
  "p95_seconds_per_record": 0.231,
  "fastest_seconds": 0.043,
  "slowest_seconds": 0.412,
  "throughput_molecules_per_minute": 481.9,
  "per_record_timings": [
    {
      "access_code": "LIG_001",
      "row": 2,
      "status": "ok",
      "seconds": 0.124,
      "stage_seconds": {
        "clean": 0.002,
        "protonate": 0.018,
        "build_3d": 0.094,
        "export": 0.010
      }
    }
  ],
  "n_jobs_used": 8,
  "started_at": "2026-05-27T12:34:56+00:00",
  "finished_at": "2026-05-27T12:35:09+00:00",
  "pdbqt_files_written": 0,
  "generated_pdbqt_files": []
}
```

## Manuscript artifacts

- `Artigo/smiles2docking_article_v2_revised.docx` — revised manuscript
  with new passages flagged in red and the new pipeline-comparison
  table.
- `Artigo/response_to_reviewer_v1.docx` — point-by-point reply to
  Reviewer #1.

## Test status

```
30 passed, 3 skipped in 2.00s
```

New tests:

- `tests/test_app_paths.py`
- `tests/test_protonator_factory.py`
- `tests/test_pipeline_parallel.py`

## Upgrade notes

- Existing `settings.yaml` files from v0.2.x will continue to work, but
  protonation will default to Dimorphite-DL. To preserve the previous
  behaviour, add `protonation.backend: openbabel`.
- The `protonation.temp_dir` and `export.output_dir` keys may now be
  left empty; the resolver will place outputs under the user-writable
  XDG/APPDATA path. To pin a specific location, set the key explicitly.
- `data/intermediate/`, `data/processed/`, `data/reports/`, and
  `data/bench_inputs/` are now in `.gitignore`.

## Acknowledgements

Reviewer #1 of *Molecular Informatics* for the detailed critique that
motivated this release.
