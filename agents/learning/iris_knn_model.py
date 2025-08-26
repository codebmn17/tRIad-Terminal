from __future__ import annotations

from pathlib import Path
import joblib
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier


ARTIFACT = Path(__file__).resolve().parents[2] / "models" / "iris_knn.joblib"


def ensure_models_dir() -> None:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)


def train_knn() -> KNeighborsClassifier:
    iris = load_iris()
    X, y = iris.data, iris.target
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(X, y)
    return model


def main() -> None:
    print("[learning] Training KNN on Iris dataset...")
    model = train_knn()
    ensure_models_dir()
    joblib.dump(model, ARTIFACT)
    print(f"[learning] Saved KNN model to {ARTIFACT}")

    # Quick demo predictions
    iris = load_iris()
    sample1 = [5.1, 3.5, 1.4, 0.2]  # setosa-like
    sample2 = [6.3, 3.3, 6.0, 2.5]  # virginica-like
    pred1 = model.predict([sample1])[0]
    pred2 = model.predict([sample2])[0]
    print({
        "model": "knn",
        "sample1": sample1,
        "pred1": iris.target_names[pred1],
        "sample2": sample2,
        "pred2": iris.target_names[pred2],
    })


if __name__ == "__main__":
    main()
