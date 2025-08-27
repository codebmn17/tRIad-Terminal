from pathlib import Path

import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier


def main() -> None:
    data = load_iris()
    X, y = data.data, data.target

    clf = KNeighborsClassifier(n_neighbors=5)
    clf.fit(X, y)

    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, models_dir / "knn_iris.joblib")


if __name__ == "__main__":
    main()
