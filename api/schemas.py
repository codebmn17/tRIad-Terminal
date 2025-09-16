"""
Pydantic models and JSON schemas for tRIad Terminal API.

This module defines all the request/response models used by the API endpoints,
with a focus on assistant functionality.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssistantStatus(BaseModel):
    """Status information for the AI assistant."""
    enabled: bool = Field(..., description="Whether the assistant is enabled")
    models_loaded: bool = Field(..., description="Whether ML models are loaded")
    training_ready: bool = Field(..., description="Whether the assistant is ready for training")
    intent_mapping_size: int = Field(..., description="Number of intent mappings available")
    last_trained: datetime | None = Field(None, description="Last training timestamp")
    capabilities: list[str] = Field(..., description="List of assistant capabilities")


class PredictCommandRequest(BaseModel):
    """Request model for command prediction."""
    prefix: str = Field("", description="Command prefix to complete")
    context: str | None = Field(None, description="Current context (e.g., directory)")
    max_suggestions: int = Field(5, ge=1, le=20, description="Maximum number of suggestions")


class PredictCommandResponse(BaseModel):
    """Response model for command prediction."""
    success: bool = Field(..., description="Whether prediction was successful")
    suggestions: list[str] = Field(..., description="List of command suggestions")
    context_used: str | None = Field(None, description="Context that was used for prediction")
    confidence_scores: list[float] | None = Field(None, description="Confidence scores for suggestions")


class NLRequest(BaseModel):
    """Request model for natural language processing."""
    nl_command: str = Field(..., description="Natural language command to process")


class NLResponse(BaseModel):
    """Response model for natural language processing."""
    success: bool = Field(..., description="Whether NL processing was successful")
    intent: str | None = Field(None, description="Detected intent")
    entities: dict[str, str] = Field(default_factory=dict, description="Extracted entities")
    command: str | None = Field(None, description="Generated shell command")
    confidence: float = Field(0.0, description="Confidence score for the result")


class CodeCompletionRequest(BaseModel):
    """Request model for code completion."""
    code_context: str = Field(..., description="Code context for completion")
    language: str = Field(..., description="Programming language")
    max_suggestions: int = Field(3, ge=1, le=10, description="Maximum number of suggestions")


class CodeCompletionResponse(BaseModel):
    """Response model for code completion."""
    success: bool = Field(..., description="Whether completion was successful")
    suggestions: list[str] = Field(..., description="List of code completion suggestions")
    language: str = Field(..., description="Programming language used")


class FeedbackRequest(BaseModel):
    """Request model for providing feedback to the assistant."""
    nl_command: str = Field(..., description="Original natural language command")
    executed_command: str = Field(..., description="Command that was executed")
    intent: str | None = Field(None, description="Intent (will be guessed if not provided)")
    success: bool = Field(True, description="Whether the command execution was successful")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool = Field(..., description="Whether feedback was processed successfully")
    message: str = Field(..., description="Result message")
    intent_guessed: str | None = Field(None, description="Intent that was guessed for the command")


class TrainRequest(BaseModel):
    """Request model for training the assistant."""
    force: bool = Field(False, description="Force retraining even if recent training exists")
    components: list[Literal["code", "commands", "nl", "all"]] | None = Field(
        ["all"], description="Which components to train"
    )


class TrainResponse(BaseModel):
    """Response model for training results."""
    success: bool = Field(..., description="Whether training was successful")
    message: str = Field(..., description="Training result message")
    components_trained: list[str] = Field(..., description="List of components that were trained")
    before_stats: dict[str, Any] = Field(..., description="Model statistics before training")
    after_stats: dict[str, Any] = Field(..., description="Model statistics after training")
    training_time_ms: float = Field(..., description="Training time in milliseconds")


class MLStatusResponse(BaseModel):
    """Response model for ML status information."""
    sklearn_available: bool = Field(..., description="Whether scikit-learn is available")
    tensorflow_available: bool = Field(..., description="Whether TensorFlow is available")
    models_initialized: dict[str, bool] = Field(..., description="Status of model initialization")
    training_data_size: dict[str, int] = Field(..., description="Size of training datasets")


class SchemaInfo(BaseModel):
    """Information about available schemas."""
    schema_name: str = Field(..., description="Name of the schema")
    description: str = Field(..., description="Description of what the schema is for")
    version: str = Field("1.0.0", description="Schema version")


class SchemaResponse(BaseModel):
    """Response model for schema information."""
    schemas: dict[str, dict[str, Any]] = Field(..., description="Available JSON schemas")
    schema_info: list[SchemaInfo] = Field(..., description="Metadata about schemas")
    api_version: str = Field("1.0.0", description="API version")


def get_assistant_schema() -> dict[str, Any]:
    """
    Return JSON Schema fragments for assistant-related models.
    
    Returns:
        Dict containing JSON schema definitions for all assistant models.
    """
    schemas = {}

    # Get schemas for all the response models
    model_classes = [
        AssistantStatus, PredictCommandResponse, CodeCompletionResponse,
        NLResponse, FeedbackResponse, TrainResponse, MLStatusResponse,
        SchemaResponse
    ]

    for model_class in model_classes:
        schema = model_class.model_json_schema()
        schemas[model_class.__name__] = schema

    return {
        "assistant_schemas": schemas,
        "version": "1.0.0",
        "description": "JSON schemas for tRIad Terminal Assistant API"
    }


# Export commonly used models
__all__ = [
    "AssistantStatus",
    "PredictCommandRequest", "PredictCommandResponse",
    "NLRequest", "NLResponse",
    "CodeCompletionRequest", "CodeCompletionResponse",
    "FeedbackRequest", "FeedbackResponse",
    "TrainRequest", "TrainResponse",
    "MLStatusResponse", "SchemaResponse",
    "get_assistant_schema"
]
