from __future__ import annotations

from .forest import predict as predict_forest
from .knn import predict as predict_knn

__all__ = ["predict_knn", "predict_forest"]
