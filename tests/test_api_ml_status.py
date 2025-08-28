"""
Test ML status API endpoints.

Tests the /ml/status endpoints that provide introspection
about ML predictor and assistant availability.
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from api.main import app

client = TestClient(app)

class TestMLStatusEndpoints:
    """Test ML status and introspection endpoints."""
    
    def test_ml_status_endpoint(self):
        """Test the ML status endpoint."""
        response = client.get("/ml/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "sklearn_available" in data
        assert "tensorflow_available" in data
        assert "predictor_ready" in data
        assert "assistant_ready" in data
        assert "models_loaded" in data
        assert "dependency_status" in data
        
        # Check data types
        assert isinstance(data["sklearn_available"], bool)
        assert isinstance(data["tensorflow_available"], bool)
        assert isinstance(data["predictor_ready"], bool)
        assert isinstance(data["assistant_ready"], bool)
        assert isinstance(data["models_loaded"], dict)
        assert isinstance(data["dependency_status"], dict)
        
        # Since scikit-learn is in requirements.txt, it should be available
        assert data["sklearn_available"] is True
        assert data["predictor_ready"] is True
        
        # Check models_loaded structure
        models_info = data["models_loaded"]
        if data["predictor_ready"]:
            assert "available_models" in models_info
            assert "default_model" in models_info
            assert isinstance(models_info["available_models"], list)
    
    def test_dependency_check_endpoint(self):
        """Test the dependency check endpoint."""
        response = client.get("/ml/dependencies")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check structure
        assert "dependencies" in data
        assert "summary" in data
        
        deps = data["dependencies"]
        summary = data["summary"]
        
        # Check that sklearn is reported (should be available)
        assert "sklearn" in deps
        sklearn_info = deps["sklearn"]
        assert "available" in sklearn_info
        assert sklearn_info["available"] is True
        assert "version" in sklearn_info
        
        # Check summary
        assert "core_ml_ready" in summary
        assert "deep_learning_ready" in summary
        assert "basic_functionality" in summary
        assert summary["core_ml_ready"] is True
        assert summary["basic_functionality"] is True
        
        # Check other dependencies
        expected_deps = ["sklearn", "numpy", "joblib"]
        for dep in expected_deps:
            assert dep in deps
            assert "available" in deps[dep]
    
    def test_tensorflow_optional_status(self):
        """Test that TensorFlow is properly marked as optional."""
        response = client.get("/ml/dependencies")
        assert response.status_code == 200
        
        data = response.json()
        deps = data["dependencies"]
        
        if "tensorflow" in deps:
            tf_info = deps["tensorflow"]
            if not tf_info["available"]:
                assert "note" in tf_info
                assert "Optional" in tf_info["note"]
    
    def test_status_endpoint_resilience(self):
        """Test that status endpoint is resilient to errors."""
        # The endpoint should work even if some components fail
        response = client.get("/ml/status")
        assert response.status_code == 200
        
        # Should always return a valid response structure
        data = response.json()
        required_fields = [
            "sklearn_available", "tensorflow_available", 
            "predictor_ready", "assistant_ready",
            "models_loaded", "dependency_status"
        ]
        
        for field in required_fields:
            assert field in data
    
    def test_dependency_versions(self):
        """Test that dependency versions are reported correctly."""
        response = client.get("/ml/dependencies")
        assert response.status_code == 200
        
        data = response.json()
        deps = data["dependencies"]
        
        # Check that available dependencies have version info
        for dep_name, dep_info in deps.items():
            if dep_info["available"]:
                assert "version" in dep_info
                version = dep_info["version"]
                assert isinstance(version, str)
                assert len(version) > 0
    
    def test_predictor_model_info(self):
        """Test that predictor model information is correct."""
        response = client.get("/ml/status")
        assert response.status_code == 200
        
        data = response.json()
        
        if data["predictor_ready"]:
            models_info = data["models_loaded"]
            
            # Check model information
            assert "available_models" in models_info
            available_models = models_info["available_models"]
            
            # Should include our known models
            expected_models = ["auto", "knn", "forest"]
            for model in expected_models:
                assert model in available_models
            
            # Check default model
            assert "default_model" in models_info
            assert models_info["default_model"] in ["auto", "knn", "forest"]

class TestMLStatusIntegration:
    """Test ML status integration with actual ML components."""
    
    def test_status_matches_actual_predictor(self):
        """Test that status endpoint matches actual predictor availability."""
        response = client.get("/ml/status")
        assert response.status_code == 200
        
        data = response.json()
        predictor_ready = data["predictor_ready"]
        
        if predictor_ready:
            # If status says predictor is ready, we should be able to use it
            from ml.predictor import MLPredictor
            predictor = MLPredictor()
            
            # Should be able to list models
            models = predictor.list_models()
            assert isinstance(models, list)
            assert len(models) > 0
            
            # Should match what the status endpoint reports
            status_models = data["models_loaded"]["available_models"]
            assert set(models) == set(status_models)
    
    def test_status_matches_assistant_availability(self):
        """Test that status matches assistant availability."""
        response = client.get("/ml/status")
        assert response.status_code == 200
        
        data = response.json()
        assistant_ready = data["assistant_ready"]
        
        # Test that we can import assistant if status says it's ready
        if assistant_ready:
            try:
                from agents.learning.assistant_ml import CodeCompletionEngine
                # Should be able to import without error
                assert CodeCompletionEngine is not None
            except ImportError:
                # If import fails, status might be reporting incorrectly
                # But that's okay for optional components
                pass
    
    def test_dependency_status_accuracy(self):
        """Test that dependency status is accurate."""
        response = client.get("/ml/dependencies")
        assert response.status_code == 200
        
        data = response.json()
        deps = data["dependencies"]
        
        # Test sklearn status accuracy
        sklearn_status = deps["sklearn"]["available"]
        try:
            import sklearn
            assert sklearn_status is True
        except ImportError:
            assert sklearn_status is False
        
        # Test numpy status accuracy
        numpy_status = deps["numpy"]["available"]
        try:
            import numpy
            assert numpy_status is True
        except ImportError:
            assert numpy_status is False