"""
Tests for assistant API endpoints.

Tests the AI assistant functionality including command prediction,
natural language processing, code completion, and training.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestAssistantEndpoints:
    """Test AI assistant endpoints."""
    
    def test_assistant_health(self):
        """Test the assistant health endpoint."""
        response = client.get("/assistant/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "assistant_available" in data
        assert "timestamp" in data
    
    def test_assistant_status(self):
        """Test the assistant status endpoint."""
        response = client.get("/assistant/status")
        
        # Should work even if assistant is not fully functional
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "enabled" in data
            assert "models_loaded" in data
            assert "training_ready" in data
            assert "intent_mapping_size" in data
            assert "capabilities" in data
            assert isinstance(data["capabilities"], list)
    
    def test_predict_command(self):
        """Test command prediction endpoint."""
        response = client.post(
            "/assistant/predict_command",
            json={
                "prefix": "ls",
                "context": "/home/user",
                "max_suggestions": 3
            }
        )
        
        # Should work even with empty model
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "suggestions" in data
            assert isinstance(data["suggestions"], list)
            assert len(data["suggestions"]) <= 3
    
    def test_process_natural_language(self):
        """Test natural language processing endpoint."""
        response = client.post(
            "/assistant/process_nl",
            json={
                "nl_command": "list files in current directory"
            }
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "confidence" in data
            assert isinstance(data["confidence"], (int, float))
    
    def test_complete_code(self):
        """Test code completion endpoint."""
        response = client.post(
            "/assistant/complete_code",
            json={
                "code_context": "def hello(",
                "language": "python",
                "max_suggestions": 2
            }
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "suggestions" in data
            assert "language" in data
            assert data["language"] == "python"
    
    def test_provide_feedback(self):
        """Test feedback endpoint."""
        response = client.post(
            "/assistant/feedback",
            json={
                "nl_command": "show files",
                "executed_command": "ls -la",
                "intent": "list_files",
                "success": True
            }
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
    
    def test_train_assistant(self):
        """Test training endpoint."""
        response = client.post(
            "/assistant/train",
            json={
                "force": False,
                "components": ["commands", "nl"]
            }
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "components_trained" in data
            assert "training_time_ms" in data
            assert isinstance(data["training_time_ms"], (int, float))
    
    def test_train_assistant_force(self):
        """Test training endpoint with force flag."""
        response = client.post(
            "/assistant/train",
            json={
                "force": True,
                "components": ["all"]
            }
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "before_stats" in data
            assert "after_stats" in data
    
    def test_ml_status(self):
        """Test ML status endpoint."""
        response = client.get("/assistant/ml_status")
        assert response.status_code == 200
        
        data = response.json()
        assert "sklearn_available" in data
        assert "tensorflow_available" in data
        assert "models_initialized" in data
        assert "training_data_size" in data
        assert isinstance(data["sklearn_available"], bool)
        assert isinstance(data["tensorflow_available"], bool)
    
    def test_get_schemas(self):
        """Test schema endpoint."""
        response = client.get("/assistant/schema")
        assert response.status_code == 200
        
        data = response.json()
        assert "schemas" in data
        assert "schema_info" in data
        assert "api_version" in data
        assert isinstance(data["schemas"], dict)
        assert isinstance(data["schema_info"], list)
        
        # Check that key schemas are present
        schemas = data["schemas"]
        expected_schemas = [
            "AssistantStatus", "PredictCommandResponse", 
            "NLResponse", "TrainResponse"
        ]
        
        for schema_name in expected_schemas:
            assert schema_name in schemas
            schema = schemas[schema_name]
            assert "properties" in schema
            assert "type" in schema
    
    def test_invalid_requests(self):
        """Test invalid request handling."""
        # Empty command prediction
        response = client.post(
            "/assistant/predict_command",
            json={"prefix": "", "max_suggestions": 0}
        )
        assert response.status_code == 422  # Validation error
        
        # Empty NL command
        response = client.post(
            "/assistant/process_nl",
            json={"nl_command": ""}
        )
        # Should handle empty command gracefully
        assert response.status_code in [200, 422, 503]
        
        # Invalid training components
        response = client.post(
            "/assistant/train",
            json={"components": ["invalid_component"]}
        )
        # Should handle invalid components gracefully
        assert response.status_code in [200, 422, 503]


class TestAssistantSchemaValidation:
    """Test that responses match their schemas."""
    
    def test_predict_command_response_schema(self):
        """Test that predict command response matches schema."""
        response = client.post(
            "/assistant/predict_command",
            json={"prefix": "ls", "max_suggestions": 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Required fields
            assert "success" in data
            assert "suggestions" in data
            assert isinstance(data["success"], bool)
            assert isinstance(data["suggestions"], list)
            
            # Optional fields should be present but can be None
            assert "context_used" in data
            assert "confidence_scores" in data
    
    def test_nl_response_schema(self):
        """Test that NL response matches schema."""
        response = client.post(
            "/assistant/process_nl",
            json={"nl_command": "list files"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Required fields
            assert "success" in data
            assert "entities" in data
            assert "confidence" in data
            assert isinstance(data["success"], bool)
            assert isinstance(data["entities"], dict)
            assert isinstance(data["confidence"], (int, float))
    
    def test_train_response_schema(self):
        """Test that train response matches schema."""
        response = client.post(
            "/assistant/train",
            json={"force": False, "components": ["commands"]}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Required fields
            required_fields = [
                "success", "message", "components_trained", 
                "before_stats", "after_stats", "training_time_ms"
            ]
            
            for field in required_fields:
                assert field in data
            
            assert isinstance(data["success"], bool)
            assert isinstance(data["message"], str)
            assert isinstance(data["components_trained"], list)
            assert isinstance(data["before_stats"], dict)
            assert isinstance(data["after_stats"], dict)
            assert isinstance(data["training_time_ms"], (int, float))