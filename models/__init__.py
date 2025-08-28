# Re-export from model.py to fix current import issue
from model import predict_knn, predict_forest

__all__ = ["predict_knn", "predict_forest"]