# Re-export from model.py to fix current import issue
from model import predict_forest, predict_knn

__all__ = ["predict_knn", "predict_forest"]
