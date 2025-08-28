"""
Machine Learning utilities and models.

This module contains ML prediction capabilities, model loading, and utilities.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

@dataclass
class IrisModels:
    """Container for trained Iris classification models."""
    knn: KNeighborsClassifier
    forest: RandomForestClassifier
    target_names: List[str]

def train_iris_models() -> IrisModels:
    """Train simple Iris classification models."""
    iris = load_iris()
    X, y = iris.data, iris.target
    target_names = list(iris.target_names)

    # Train KNN model
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X, y)

    # Train Random Forest model
    forest = RandomForestClassifier(n_estimators=100, random_state=42)
    forest.fit(X, y)

    return IrisModels(knn=knn, forest=forest, target_names=target_names)

class MLPredictor:
    """Main ML predictor class with multiple model support."""
    
    def __init__(self):
        """Initialize the predictor with trained models."""
        self.models = train_iris_models()
        self.default_model = "auto"
    
    def predict(self, features: List[float], model_type: str = "auto") -> Dict[str, Any]:
        """
        Make a prediction using the specified model.
        
        Args:
            features: List of numeric features
            model_type: Type of model to use ("auto", "knn", "forest")
            
        Returns:
            Dictionary with prediction results
        """
        start_time = time.time()
        
        # Determine which model to use
        if model_type == "auto":
            # Use Random Forest as default for "auto"
            model_type = "forest"
        
        if model_type == "knn":
            model = self.models.knn
        elif model_type == "forest":
            model = self.models.forest
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Validate features for Iris dataset (should be 4 features)
        if len(features) != 4:
            # For this stub, we'll pad or truncate to 4 features
            if len(features) < 4:
                features = features + [0.0] * (4 - len(features))
            else:
                features = features[:4]
        
        # Make prediction
        probs = model.predict_proba([features])[0]
        label_idx = int(probs.argmax())
        predicted_label = self.models.target_names[label_idx]
        confidence = float(probs.max())
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "prediction": {
                "label": predicted_label,
                "index": label_idx,
                "probabilities": {
                    self.models.target_names[i]: float(p) 
                    for i, p in enumerate(probs)
                }
            },
            "model_used": model_type,
            "confidence": confidence,
            "processing_time_ms": processing_time
        }
    
    def list_models(self) -> List[str]:
        """List available model types."""
        return ["auto", "knn", "forest"]

# Legacy functions for backward compatibility
def predict_knn(features: List[float]) -> Dict[str, Any]:
    """Legacy KNN prediction function for backward compatibility."""
    predictor = MLPredictor()
    result = predictor.predict(features, "knn")
    
    # Format to match legacy output
    prediction = result["prediction"]
    return {
        "model": "knn",
        "predicted_index": prediction["index"],
        "predicted_label": prediction["label"],
        "probabilities": prediction["probabilities"]
    }

def predict_forest(features: List[float]) -> Dict[str, Any]:
    """Legacy Random Forest prediction function for backward compatibility."""
    predictor = MLPredictor()
    result = predictor.predict(features, "forest")
    
    # Format to match legacy output
    prediction = result["prediction"]
    return {
        "model": "forest",
        "predicted_index": prediction["index"],
        "predicted_label": prediction["label"],
        "probabilities": prediction["probabilities"]
    }