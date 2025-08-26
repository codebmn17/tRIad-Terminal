# Iris K-Nearest Neighbors Model Training and Prediction
# This script demonstrates training a KNN model on the Iris dataset,
# saving it with joblib, and then loading it to make predictions.

import joblib
from sklearn.neighbors import KNeighborsClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
import numpy as np

# Load the iris dataset
iris = load_iris()
X = iris.data
y = iris.target

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("=== Iris Dataset KNN Model Training ===")
print(f"Dataset shape: {X.shape}")
print(f"Training set: {X_train.shape[0]} samples")
print(f"Test set: {X_test.shape[0]} samples")
print(f"Classes: {iris.target_names}")
print("-" * 50)

# Find the best k value (optional step to demonstrate tuning)
print("--- Finding Optimal K Value ---")
k_values = range(1, 21)
cv_scores = []

for k in k_values:
    knn = KNeighborsClassifier(n_neighbors=k)
    scores = cross_val_score(knn, X_train, y_train, cv=5, scoring='accuracy')
    cv_scores.append(scores.mean())

best_k = k_values[np.argmax(cv_scores)]
best_score = max(cv_scores)

print(f"Best k value: {best_k}")
print(f"Best cross-validation accuracy: {best_score:.4f}")
print("-" * 50)

# We'll use the best k we found (or set it to 7 as per your example)
best_k = 7  # You can use the actual best_k found above

# --- Part 1: Train and Save the Final Model ---

print("--- Training Final Model ---")
# 1. Create and train the final model using the optimal k value
final_model = KNeighborsClassifier(n_neighbors=best_k)
final_model.fit(X_train, y_train)
print(f"Final model trained with k={best_k}.")

# 2. Define the filename for our saved model
filename = 'final_iris_knn_model.joblib'

# 3. Use joblib to dump the trained model into a file
joblib.dump(final_model, filename)
print(f"Model saved successfully to '{filename}'")
print("-" * 30 + "\n")

# --- Part 2: Load the Model and Make a Prediction ---

print("--- Loading Model and Making a New Prediction ---")
# This part simulates how you would use the model in a different program
# or after restarting your computer.

# 1. Load the model from the file
loaded_model = joblib.load(filename)
print("Model loaded successfully from file.")

# 2. Create some new data to test the loaded model
#    Features are: [sepal length (cm), sepal width (cm), petal length (cm), petal width (cm)]
#    This sample data strongly resembles an Iris-Virginica
new_iris_data = [[5.9, 3.0, 5.1, 1.8]] 

# 3. Use the loaded model to make a prediction
#    The .predict() method expects a 2D array, so we use [[...]]
prediction_result = loaded_model.predict(new_iris_data)

# 4. The result is a number (0, 1, or 2). Let's get the actual species name.
#    We can use the `target_names` from our original `iris` object.
predicted_species_name = iris.target_names[prediction_result[0]]

print(f"\nNew data sample: {new_iris_data}")
print(f"The loaded model predicts the species is: '{predicted_species_name}'")

# Additional demonstration with multiple predictions
print("\n--- Testing with Multiple Samples ---")
test_samples = [
    [5.1, 3.5, 1.4, 0.2],  # Typical Setosa
    [7.0, 3.2, 4.7, 1.4],  # Typical Versicolor  
    [6.3, 3.3, 6.0, 2.5]   # Typical Virginica
]

for i, sample in enumerate(test_samples):
    prediction = loaded_model.predict([sample])
    species = iris.target_names[prediction[0]]
    print(f"Sample {i+1}: {sample} -> Predicted: {species}")

# Test accuracy on the test set
test_accuracy = loaded_model.score(X_test, y_test)
print(f"\nModel accuracy on test set: {test_accuracy:.4f}")

print("\n=== Model Training and Testing Complete ===")
# ==== wrapper + caching for production use ====
import os
from pathlib import Path
import joblib
import numpy as np
from sklearn.datasets import load_iris

_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "iris_knn.joblib"
_MODEL = None
_TARGET_NAMES = load_iris().target_names  # ["setosa", "versicolor", "virginica"]

def _ensure_model():
    """Load the trained KNN once (or train & save if missing)."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if _MODEL_PATH.exists():
        _MODEL = joblib.load(_MODEL_PATH)
        return _MODEL

    # Train quickly if artifact is missing (safe fallback)
    iris = load_iris()
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42
    )
    model = KNeighborsClassifier(n_neighbors=7)
    model.fit(X_train, y_train)
    _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, _MODEL_PATH)
    _MODEL = model
    return _MODEL

def predict(x):
    """
    x: [sepal_length, sepal_width, petal_length, petal_width]
    returns: {"model": "knn", "label": "...", "proba": {"setosa": 0.12, ...}, "features": x}
    """
    m = _ensure_model()
    xx = np.array([x], dtype=float)
    y = int(m.predict(xx)[0])

    # If classifier supports predict_proba (KNN does)
    proba = {}
    if hasattr(m, "predict_proba"):
        p = m.predict_proba(xx)[0]
        for name, val in zip(_TARGET_NAMES, p):
            proba[name] = float(val)

    return {"model": "knn", "label": _TARGET_NAMES[y], "proba": proba, "features": x}

# ---- keep your printed demo ONLY when run as a script ----
if __name__ == "__main__":
    # Your existing training/printing demo can stay here.
    # It will no longer run when the module is imported.
    pass
