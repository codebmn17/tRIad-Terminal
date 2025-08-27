from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier


def main() -> None:
    data = load_iris()
    X, y = data.data, data.target

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)

    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, models_dir / "random_forest_iris.joblib")


if __name__ == "__main__":
    main()
