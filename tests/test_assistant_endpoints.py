"""
Test AI Assistant API endpoints.

Tests the /assistant endpoints for command prediction, code completion,
natural language processing, and feedback handling.
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

class TestAssistantStatusEndpoint:
    """Test assistant status endpoint."""
    
    def test_assistant_status(self):
        """Test the assistant status endpoint."""
        response = client.get("/assistant/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "available" in data
        assert "sklearn_available" in data
        assert "models_trained" in data
        assert "supported_languages" in data
        assert "features" in data
        
        # Check data types
        assert isinstance(data["available"], bool)
        assert isinstance(data["sklearn_available"], bool)
        assert isinstance(data["models_trained"], bool)
        assert isinstance(data["supported_languages"], list)
        assert isinstance(data["features"], dict)
        
        # Check supported languages
        languages = data["supported_languages"]
        expected_languages = ["python", "javascript", "bash"]
        for lang in expected_languages:
            assert lang in languages
        
        # Check features
        features = data["features"]
        expected_features = [
            "command_prediction", "code_completion", 
            "natural_language", "machine_learning"
        ]
        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], bool)
        
        # Basic functionality should always be available via heuristics
        assert features["command_prediction"] is True
        assert features["code_completion"] is True
        assert features["natural_language"] is True

class TestCommandPredictionEndpoint:
    """Test command prediction endpoint."""
    
    def test_predict_command_basic(self):
        """Test basic command prediction."""
        request_data = {
            "context": "ls",
            "history": [],
            "max_suggestions": 5
        }
        
        response = client.post("/assistant/predict_command", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check response structure
        assert "suggestions" in data
        assert "source" in data
        assert isinstance(data["suggestions"], list)
        assert data["source"] in ["ml", "heuristic"]
        
        # Should have at least one suggestion
        assert len(data["suggestions"]) > 0
        
        # All suggestions should be strings
        for suggestion in data["suggestions"]:
            assert isinstance(suggestion, str)
    
    def test_predict_command_with_history(self):
        """Test command prediction with history context."""
        request_data = {
            "context": "cd",
            "history": ["ls", "pwd", "mkdir test"],
            "max_suggestions": 3
        }
        
        response = client.post("/assistant/predict_command", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["suggestions"]) <= 3
        assert isinstance(data["suggestions"], list)
    
    def test_predict_command_empty_context(self):
        """Test command prediction with empty context."""
        request_data = {
            "context": "",
            "history": []
        }
        
        response = client.post("/assistant/predict_command", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should still provide suggestions even with empty context
        assert len(data["suggestions"]) > 0
    
    def test_predict_command_max_suggestions(self):
        """Test that max_suggestions parameter is respected."""
        request_data = {
            "context": "git",
            "max_suggestions": 2
        }
        
        response = client.post("/assistant/predict_command", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["suggestions"]) <= 2

class TestCodeCompletionEndpoint:
    """Test code completion endpoint."""
    
    def test_complete_code_python(self):
        """Test Python code completion."""
        request_data = {
            "code": "def hello_world():",
            "language": "python",
            "max_completions": 5
        }
        
        response = client.post("/assistant/complete_code", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check response structure
        assert "completions" in data
        assert "source" in data
        assert isinstance(data["completions"], list)
        assert data["source"] in ["ml", "heuristic"]
        
        # Should have at least one completion
        assert len(data["completions"]) > 0
        
        # All completions should be strings
        for completion in data["completions"]:
            assert isinstance(completion, str)
    
    def test_complete_code_javascript(self):
        """Test JavaScript code completion."""
        request_data = {
            "code": "function test() {",
            "language": "javascript"
        }
        
        response = client.post("/assistant/complete_code", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["completions"]) > 0
    
    def test_complete_code_bash(self):
        """Test Bash code completion."""
        request_data = {
            "code": "#!/bin/bash\necho",
            "language": "bash"
        }
        
        response = client.post("/assistant/complete_code", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["completions"]) > 0
    
    def test_complete_code_empty(self):
        """Test code completion with empty code."""
        request_data = {
            "code": "",
            "language": "python"
        }
        
        response = client.post("/assistant/complete_code", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should still provide completions for empty code
        assert len(data["completions"]) > 0
    
    def test_complete_code_max_completions(self):
        """Test that max_completions parameter is respected."""
        request_data = {
            "code": "import",
            "language": "python",
            "max_completions": 3
        }
        
        response = client.post("/assistant/complete_code", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["completions"]) <= 3

class TestNaturalLanguageEndpoint:
    """Test natural language processing endpoint."""
    
    def test_nl_intent_recognition(self):
        """Test intent recognition."""
        request_data = {
            "text": "How do I create a new file?",
            "task": "intent"
        }
        
        response = client.post("/assistant/nl", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check response structure
        assert "result" in data
        assert isinstance(data["result"], str)
        
        # Should detect help intent
        assert data["result"] == "help_request"
    
    def test_nl_command_translation(self):
        """Test command translation."""
        request_data = {
            "text": "list files in current directory",
            "task": "command"
        }
        
        response = client.post("/assistant/nl", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should translate to ls command
        assert data["result"] == "ls"
        assert "confidence" in data
        assert "metadata" in data
    
    def test_nl_creation_intent(self):
        """Test creation intent recognition."""
        request_data = {
            "text": "I want to create a new directory",
            "task": "intent"
        }
        
        response = client.post("/assistant/nl", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["result"] == "creation_request"
    
    def test_nl_deletion_intent(self):
        """Test deletion intent recognition."""
        request_data = {
            "text": "Remove this file please",
            "task": "intent"
        }
        
        response = client.post("/assistant/nl", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["result"] == "deletion_request"
    
    def test_nl_unsupported_task(self):
        """Test handling of unsupported task."""
        request_data = {
            "text": "Hello world",
            "task": "unsupported_task"
        }
        
        response = client.post("/assistant/nl", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "not supported" in data["result"]
        assert data["confidence"] == 0.0
    
    def test_nl_unknown_command(self):
        """Test handling of unknown command translation."""
        request_data = {
            "text": "do something completely unknown",
            "task": "command"
        }
        
        response = client.post("/assistant/nl", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "couldn't translate" in data["result"]
        assert data["confidence"] == 0.0

class TestFeedbackEndpoint:
    """Test feedback handling endpoint."""
    
    def test_provide_positive_feedback(self):
        """Test providing positive feedback."""
        request_data = {
            "feedback_type": "positive",
            "context": "Command prediction was helpful"
        }
        
        response = client.post("/assistant/feedback", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "message" in data
        assert "feedback_id" in data
        
        assert data["status"] == "received"
        assert "positive" in data["message"]
    
    def test_provide_negative_feedback(self):
        """Test providing negative feedback."""
        request_data = {
            "feedback_type": "negative",
            "suggestion": "ls -la would be better",
            "context": "Wrong command suggested"
        }
        
        response = client.post("/assistant/feedback", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "received"
        assert "negative" in data["message"]
    
    def test_provide_correction_feedback(self):
        """Test providing correction feedback."""
        request_data = {
            "feedback_type": "correction",
            "suggestion": "mkdir should be suggested instead of touch",
            "prediction_id": "pred_123"
        }
        
        response = client.post("/assistant/feedback", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "received"
        assert "correction" in data["message"]

class TestAssistantEndpointIntegration:
    """Test integration of assistant endpoints."""
    
    def test_workflow_command_prediction_to_feedback(self):
        """Test complete workflow from prediction to feedback."""
        # 1. Get command prediction
        predict_request = {
            "context": "git",
            "max_suggestions": 3
        }
        
        predict_response = client.post("/assistant/predict_command", json=predict_request)
        assert predict_response.status_code == 200
        
        predict_data = predict_response.json()
        suggestions = predict_data["suggestions"]
        
        # 2. Provide feedback on the prediction
        feedback_request = {
            "feedback_type": "positive",
            "context": f"Suggestion '{suggestions[0]}' was helpful"
        }
        
        feedback_response = client.post("/assistant/feedback", json=feedback_request)
        assert feedback_response.status_code == 200
        
        feedback_data = feedback_response.json()
        assert feedback_data["status"] == "received"
    
    def test_code_completion_workflow(self):
        """Test code completion workflow."""
        # Get code completion
        completion_request = {
            "code": "def calculate_",
            "language": "python"
        }
        
        response = client.post("/assistant/complete_code", json=completion_request)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["completions"]) > 0
        assert data["source"] in ["ml", "heuristic"]
    
    def test_natural_language_workflow(self):
        """Test natural language processing workflow."""
        # Process natural language for intent
        nl_request = {
            "text": "Help me understand git commands",
            "task": "intent"
        }
        
        response = client.post("/assistant/nl", json=nl_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["result"] == "help_request"
        
        # Process for command translation
        command_request = {
            "text": "show current directory",
            "task": "command"
        }
        
        response = client.post("/assistant/nl", json=command_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["result"] == "pwd"