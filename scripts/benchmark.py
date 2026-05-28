"""Throughput benchmark for SMILES2Docking.

Measures wall-clock seconds to prepare N ligands at varying worker
counts. Designed to support the scalability discussion requested by
Reviewer #4.

Usage:
    python scripts/benchmark.py --sizes 100 1000 --jobs 1 4 8 \
        --input data/raw/zinc_sample.csv --protonation-backend dimorphite

Outputs a CSV at data/reports/benchmark_<timestamp>.csv with columns:
    size, n_jobs, backend, protonation_backend, mopac_enabled,
    seconds, molecules_per_minute
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import load_settings, resolve_settings_paths  # noqa: E402
from src.workflow.pipeline import run_workflow  # noqa: E402


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.WARNING)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def _trimmed_input(original_path: Path, size: int, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    trimmed = work_dir / f"input_{size}{original_path.suffix.lower() or '.csv'}"
    with original_path.open("r", encoding="utf-8") as src, trimmed.open("w", encoding="utf-8") as dst:
        header = src.readline()
        dst.write(header)
        for _ in range(size):
            line = src.readline()
            if not line:
                break
            dst.write(line)
    return trimmed


def _run_one(
    base_settings: dict,
    input_path: Path,
    n_jobs: int,
    protonation_backend: str,
    mopac_enabled: bool,
) -> float:
    settings = deepcopy(base_settings)
    settings.setdefault("input", {})["file_path"] = str(input_path)
    settings.setdefault("parallel", {})["enabled"] = n_jobs != 1
    settings["parallel"]["n_jobs"] = n_jobs
    settings.setdefault("protonation", {})["backend"] = protonation_backend
    settings.setdefault("pm7", {})["enabled"] = mopac_enabled
    resolved = resolve_settings_paths(settings)

    logger = _build_logger()
    start = time.perf_counter()
    run_workflow(resolved, logger)
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark SMILES2Docking throughput.")
    parser.add_argument("--input", required=True, help="Path to a large SMILES CSV/XLSX source.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 1000])
    parser.add_argument("--jobs", nargs="+", type=int, default=[1, 4, 8])
    parser.add_argument(
        "--protonation-backend",
        default="dimorphite",
        choices=["dimorphite", "openbabel", "none"],
    )
    parser.add_argument("--mopac", action="store_true", help="Enable MOPAC PM7 refinement.")
    parser.add_argument("--config", default=None, help="Optional settings.yaml override.")
    parser.add_argument("--output", default=None, help="CSV output path.")
    args = parser.parse_args()

    base_settings = load_settings(args.config)
    source_path = Path(args.input).resolve()
    if not source_path.exists():
        raise SystemExit(f"Input file not found: {source_path}")

    work_dir = PROJECT_ROOT / "data" / "bench_inputs"
    rows: list[dict] = []

    for size in args.sizes:
        trimmed = _trimmed_input(source_path, size, work_dir)
        for n_jobs in args.jobs:
            elapsed = _run_one(
                base_settings,
                trimmed,
                n_jobs,
                args.protonation_backend,
                args.mopac,
            )
            mpm = (size / elapsed) * 60.0 if elapsed > 0 else 0.0
            rows.append(
                {
                    "size": size,
                    "n_jobs": n_jobs,
                    "backend": "joblib" if n_jobs != 1 else "sequential",
                    "protonation_backend": args.protonation_backend,
                    "mopac_enabled": args.mopac,
                    "seconds": round(elapsed, 3),
                    "molecules_per_minute": round(mpm, 1),
                }
            )
            print(f"[bench] size={size} n_jobs={n_jobs} elapsed={elapsed:.2f}s mpm={mpm:.1f}")

    if not rows:
        raise SystemExit("No benchmark rows produced.")
    output_path = Path(args.output) if args.output else (
        PROJECT_ROOT / "data" / "reports" / f"benchmark_{datetime.now():%Y%m%d_%H%M%S}.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[bench] wrote {output_path}")


if __name__ == "__main__":
    main()
