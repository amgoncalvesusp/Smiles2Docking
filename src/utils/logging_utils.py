from __future__ import annotations

import logging
from pathlib import Path
from typing import Any


def resolve_log_path(settings: dict[str, Any]) -> Path:
    log_dir = Path(settings["logging"]["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    file_name = settings["logging"].get("file_name", "workflow.log")
    return log_dir / file_name


def setup_logging(settings: dict[str, Any]) -> logging.Logger:
    log_path = resolve_log_path(settings)
    logger = logging.getLogger("smiles2docking")
    logger.setLevel(getattr(logging, settings["logging"].get("level", "INFO").upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
