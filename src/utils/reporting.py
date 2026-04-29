from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.utils.models import RunReport


def write_report(report: RunReport, report_dir: str) -> Path:
    target_dir = Path(report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = target_dir / f"run_report_{timestamp}.json"
    payload = asdict(report)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path
