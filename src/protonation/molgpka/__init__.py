"""Vendored MolGpKa inference (MIT). See LICENSE.md in this directory."""

from __future__ import annotations

from .predict_pka import predict, predict_acid, predict_base

__all__ = ["predict", "predict_acid", "predict_base"]
