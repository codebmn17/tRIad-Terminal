"""
Test suite for the production API endpoints.

Tests health checks, ML predictions, and general API functionality.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from api.main import app

# Create test client
client = TestClient(app)

class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "tRIad-Terminal-API"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "tRIad Terminal API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "endpoints" in data
        assert "timestamp" in data

class TestMLEndpoints:
    """Test machine learning endpoints."""

    def test_ml_predict_valid_input(self):
        """Test ML prediction with valid input."""
        test_features = [5.1, 3.5, 1.4, 0.2]  # Valid iris features

        response = client.post(
            "/ml/predict",
            json={"features": test_features}
        )

        assert response.status_code == 200
        data = response.json()

        assert "prediction" in data
        assert "model_used" in data
        assert "confidence" in data
        assert "processing_time_ms" in data

        # Check prediction structure
        prediction = data["prediction"]
        assert "label" in prediction
        assert "index" in prediction
        assert "probabilities" in prediction

    def test_ml_predict_with_model_type(self):
        """Test ML prediction with specific model type."""
        test_features = [6.2, 2.8, 4.8, 1.8]

        response = client.post(
            "/ml/predict",
            json={"features": test_features, "model_type": "knn"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model_used"] == "knn"

    def test_ml_predict_invalid_features_empty(self):
        """Test ML prediction with empty features."""
        response = client.post(
            "/ml/predict",
            json={"features": []}
        )

        assert response.status_code == 422  # Validation error

    def test_ml_predict_invalid_features_non_numeric(self):
        """Test ML prediction with non-numeric features."""
        response = client.post(
            "/ml/predict",
            json={"features": ["a", "b", "c", "d"]}
        )

        assert response.status_code == 422  # Validation error

    def test_ml_predict_wrong_feature_count(self):
        """Test ML prediction with wrong number of features."""
        # This should still work as we pad/truncate features
        response = client.post(
            "/ml/predict",
            json={"features": [1.0, 2.0]}  # Only 2 features instead of 4
        )

        assert response.status_code == 200  # Should work with padding

    def test_list_models(self):
        """Test the list models endpoint."""
        response = client.get("/ml/models")
        assert response.status_code == 200

        data = response.json()
        assert "available_models" in data
        assert "default_model" in data
        assert "model_info" in data

        assert isinstance(data["available_models"], list)
        assert len(data["available_models"]) > 0

class TestAPIStructure:
    """Test general API structure and configuration."""

    def test_api_docs_available(self):
        """Test that API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self):
        """Test that ReDoc documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "tRIad Terminal API"
        assert schema["info"]["version"] == "1.0.0"

def test_backward_compatibility():
    """Test that ML functions work for backward compatibility."""
    from ml.predictor import predict_forest, predict_knn

    test_features = [5.1, 3.5, 1.4, 0.2]

    # Test KNN
    knn_result = predict_knn(test_features)
    assert "model" in knn_result
    assert knn_result["model"] == "knn"
    assert "predicted_index" in knn_result
    assert "predicted_label" in knn_result
    assert "probabilities" in knn_result

    # Test Random Forest
    forest_result = predict_forest(test_features)
    assert "model" in forest_result
    assert forest_result["model"] == "forest"
    assert "predicted_index" in forest_result
    assert "predicted_label" in forest_result
    assert "probabilities" in forest_result

if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v"])
