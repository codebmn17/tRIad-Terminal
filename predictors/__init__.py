from __future__ import annotations

from .knn import predict as predict_knn
from .forest import predict as predict_forest

__all__ = ["predict_knn", "predict_forest"]
