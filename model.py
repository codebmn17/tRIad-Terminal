from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

@dataclass
class IrisModels:
    """Train and serve simple Iris classifiers (KNN and RandomForest)."""
    knn: KNeighborsClassifier
    forest: RandomForestClassifier
    target_names: List[str]

def train_iris_models() -> IrisModels:
    iris = load_iris()
    X, y = iris.data, iris.target
    target_names = list(iris.target_names)

    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X, y)

    forest = RandomForestClassifier(n_estimators=200, random_state=42)
    forest.fit(X, y)

    return IrisModels(knn=knn, forest=forest, target_names=target_names)

# Train once at import (fast; dataset is tiny)
MODELS = train_iris_models()

def predict_knn(features: List[float]) -> Dict[str, Any]:
    probs = MODELS.knn.predict_proba([features])[0]
    label_idx = int(probs.argmax())
    return {
        "model": "knn",
        "predicted_index": label_idx,
        "predicted_label": MODELS.target_names[label_idx],
        "probabilities": {MODELS.target_names[i]: float(p) for i, p in enumerate(probs)}
    }

def predict_forest(features: List[float]) -> Dict[str, Any]:
    probs = MODELS.forest.predict_proba([features])[0]
    label_idx = int(probs.argmax())
    return {
        "model": "forest",
        "predicted_index": label_idx,
        "predicted_label": MODELS.target_names[label_idx],
        "probabilities": {MODELS.target_names[i]: float(p) for i, p in enumerate(probs)}
    }
