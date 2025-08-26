from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier

# Cache target names once to avoid repeated dataset loads
_TARGET_NAMES = load_iris().target_names

# Artifact path and in-memory cache
_ARTIFACT = Path(__file__).resolve().parent.parent / "models" / "iris_knn.joblib"
_MODEL: KNeighborsClassifier | None = None

_FEATURE_NAMES = (
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
)

def _ensure_models_dir() -> None:
    models_dir = _ARTIFACT.parent
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)

def _train_and_save() -> KNeighborsClassifier:
    iris = load_iris()
    X, y = iris.data, iris.target
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(X, y)
    _ensure_models_dir()
    joblib.dump(model, _ARTIFACT)
    return model

def _ensure_model() -> KNeighborsClassifier:
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if _ARTIFACT.exists():
        _MODEL = joblib.load(_ARTIFACT)
        return _MODEL
    _MODEL = _train_and_save()
    return _MODEL

def _validate_x(x: List[float]) -> List[float]:
    # Accept list, tuple, or numpy array
    if isinstance(x, np.ndarray):
        if x.ndim != 1 or x.size != 4:
            raise ValueError("x must be a 1D array of length 4")
        try:
            return x.astype(float).ravel().tolist()
        except (ValueError, TypeError) as e:
            raise ValueError("x must contain only numeric values") from e

    if not isinstance(x, (list, tuple)):
        raise ValueError("x must be a list or tuple of 4 numeric features")
    if len(x) != 4:
        raise ValueError("x must have length 4: [sepal_length, sepal_width, petal_length, petal_width]")
    try:
        xf = [float(v) for v in x]
    except (ValueError, TypeError) as e:
        raise ValueError("x must contain only numeric values") from e
    return xf

def predict(x: List[float]) -> Dict[str, Any]:
    """Predict Iris class using the cached KNN model.

    Args:
        x: [sepal_length, sepal_width, petal_length, petal_width]

    Returns:
        Dict with keys: model, label, proba, features
    """
    xf = _validate_x(x)
    model = _ensure_model()

    class_ids = list(model.classes_)  # e.g., [0,1,2]

    X = np.asarray([xf], dtype=float)
    probs = model.predict_proba(X)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = _TARGET_NAMES[class_ids[pred_idx]]

    proba_map = {_TARGET_NAMES[c]: float(p) for c, p in zip(class_ids, probs)}
    features_map = {name: float(val) for name, val in zip(_FEATURE_NAMES, xf)}

    return {
        "model": "knn",
        "label": str(pred_label),
        "proba": proba_map,
        "features": features_map,
    }