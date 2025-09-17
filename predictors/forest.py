import os
from typing import Any

import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

# Cache target names once
_TARGET_NAMES: list[str] | None = None

# Cache model instance in-memory
_MODEL: RandomForestClassifier | None = None

# Model artifact path
_MODEL_DIR = "models"
_MODEL_PATH = os.path.join(_MODEL_DIR, "random_forest_iris.joblib")

# Feature names for echoing inputs back
_FEATURE_NAMES = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def _get_target_names() -> list[str]:
    global _TARGET_NAMES
    if _TARGET_NAMES is None:
        _TARGET_NAMES = load_iris().target_names.tolist()
    return _TARGET_NAMES


def _ensure_model_dir() -> None:
    os.makedirs(_MODEL_DIR, exist_ok=True)


def _train_and_persist_model() -> RandomForestClassifier:
    data = load_iris()
    X, y = data.data, data.target
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    _ensure_model_dir()
    joblib.dump(clf, _MODEL_PATH)
    return clf


def _load_or_train_model() -> RandomForestClassifier:
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if os.path.exists(_MODEL_PATH):
        _MODEL = joblib.load(_MODEL_PATH)
        return _MODEL
    _MODEL = _train_and_persist_model()
    return _MODEL


def _validate_x(x: list[float]) -> list[float]:
 copilot/fix-1f51a615-a20d-476a-b14f-a5ee1cba80a2
    if not isinstance(x, list | tuple):

    if not isinstance(x, (list, tuple)):
 main
        raise ValueError("x must be a list of 4 numeric values.")
    if len(x) != 4:
        raise ValueError(
            "x must have length 4: [sepal_length, sepal_width, petal_length, petal_width]."
        )
    try:
        floats = [float(v) for v in x]
    except Exception as e:
        raise ValueError(f"x must be numeric: {e}") from e
    return floats


def predict(x: list[float]) -> dict[str, Any]:
    """
    Predict using a cached RandomForestClassifier trained on the Iris dataset.

    Input:
      x: [sepal_length, sepal_width, petal_length, petal_width]

    Returns schema identical to KNN:
      {
        "model": "forest",
        "label": "<species>",
        "proba": { "<species>": float, ... },
        "features": { "sepal_length": float, ... }
      }
    """
    features = _validate_x(x)
    model = _load_or_train_model()
    target_names = _get_target_names()

    X = np.array([features], dtype=float)
    proba_arr = model.predict_proba(X)[0]  # shape: (n_classes,)
    pred_idx = int(model.predict(X)[0])

    # Map probabilities to target labels; ensure class order mapping
    class_labels = [target_names[int(c)] for c in model.classes_]
    proba_map = {cls: float(p) for cls, p in zip(class_labels, proba_arr, strict=False)}

    result = {
        "model": "forest",
        "label": target_names[pred_idx],
        "proba": proba_map,
        "features": {k: float(v) for k, v in zip(_FEATURE_NAMES, features, strict=False)},
    }
    return result
