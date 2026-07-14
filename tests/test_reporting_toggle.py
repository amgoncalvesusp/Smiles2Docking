"""The JSON audit report is written only when reporting is enabled."""

from __future__ import annotations

from pathlib import Path

from src.utils.models import RunReport
from src.workflow.pipeline import _write_report


def test_report_written_when_enabled(tmp_path: Path) -> None:
    report = RunReport(input_file="x.csv")
    settings = {"reporting": {"enabled": True, "report_dir": str(tmp_path)}}
    path = _write_report(report, settings)
    assert path
    assert Path(path).exists()


def test_report_skipped_when_disabled(tmp_path: Path) -> None:
    report = RunReport(input_file="x.csv")
    settings = {"reporting": {"enabled": False, "report_dir": str(tmp_path)}}
    assert _write_report(report, settings) == ""
    assert not any(tmp_path.iterdir())


def test_report_defaults_to_enabled(tmp_path: Path) -> None:
    report = RunReport(input_file="x.csv")
    settings = {"reporting": {"report_dir": str(tmp_path)}}
    assert _write_report(report, settings)
