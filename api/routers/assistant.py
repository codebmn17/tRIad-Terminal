"""
Assistant API endpoints for tRIad Terminal.

Provides AI assistant functionality including command prediction,
natural language processing, code completion, and training.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from fastapi import APIRouter, HTTPException

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.schemas import (
    AssistantStatus,
    CodeCompletionRequest,
    CodeCompletionResponse,
    FeedbackRequest,
    FeedbackResponse,
    MLStatusResponse,
    NLRequest,
    NLResponse,
    PredictCommandRequest,
    PredictCommandResponse,
    SchemaResponse,
    TrainRequest,
    TrainResponse,
    get_assistant_schema,
)

# Import the AI assistant
try:
    from agents.learning.assistant_ml import AIAssistant
    ASSISTANT_AVAILABLE = True
except ImportError:
    try:
        # Fallback to the current file name
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "assistant_ml",
            os.path.join(project_root, "agents", "learning", "assistant-ML.py")
        )
        assistant_ml = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assistant_ml)
        AIAssistant = assistant_ml.AIAssistant
        ASSISTANT_AVAILABLE = True
    except Exception as e:
        print(f"Warning: Could not import AI assistant: {e}")
        ASSISTANT_AVAILABLE = False
        AIAssistant = None

router = APIRouter()

# Initialize the AI assistant
_assistant_instance = None

def get_assistant() -> AIAssistant:
    """Get or create the AI assistant instance."""
    global _assistant_instance
    if not ASSISTANT_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Assistant not available")

    if _assistant_instance is None:
        _assistant_instance = AIAssistant()

    return _assistant_instance


@router.get("/status", response_model=AssistantStatus)
async def get_assistant_status() -> AssistantStatus:
    """
    Get the current status of the AI assistant.
    
    Returns comprehensive information about the assistant's state,
    including model status, training readiness, and capabilities.
    """
    try:
        assistant = get_assistant()
        status_data = assistant.status()

        return AssistantStatus(**status_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assistant status: {str(e)}"
        ) from e


@router.post("/predict_command", response_model=PredictCommandResponse)
async def predict_command(request: PredictCommandRequest) -> PredictCommandResponse:
    """
    Predict the next command based on prefix and context.
    
    Uses command history and ML models to suggest likely next commands.
    """
    try:
        assistant = get_assistant()

        suggestions = assistant.predict_command(
            prefix=request.prefix
        )

        # Set context if provided
        if request.context:
            assistant.set_context(request.context)

        # Get context-aware suggestions
        context_suggestions = assistant.predict_command(
            prefix=request.prefix
        )[:request.max_suggestions]

        return PredictCommandResponse(
            success=True,
            suggestions=context_suggestions,
            context_used=request.context,
            confidence_scores=None  # Could be enhanced later
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Command prediction failed: {str(e)}"
        ) from e


@router.post("/process_nl", response_model=NLResponse)
async def process_natural_language(request: NLRequest) -> NLResponse:
    """
    Process natural language command and convert to shell command.
    
    Uses NLP models to understand intent and generate appropriate commands.
    """
    try:
        assistant = get_assistant()

        result = assistant.process_nl_command(request.nl_command)

        return NLResponse(
            success=result.get("success", False),
            intent=result.get("intent"),
            entities=result.get("entities", {}),
            command=result.get("command"),
            confidence=result.get("confidence", 0.0)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Natural language processing failed: {str(e)}"
        ) from e


@router.post("/complete_code", response_model=CodeCompletionResponse)
async def complete_code(request: CodeCompletionRequest) -> CodeCompletionResponse:
    """
    Get code completion suggestions for the given context.
    
    Provides intelligent code suggestions based on context and language.
    """
    try:
        assistant = get_assistant()

        suggestions = assistant.complete_code(
            code_context=request.code_context,
            language=request.language
        )

        # Limit suggestions to requested amount
        limited_suggestions = suggestions[:request.max_suggestions]

        return CodeCompletionResponse(
            success=len(limited_suggestions) > 0,
            suggestions=limited_suggestions,
            language=request.language
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code completion failed: {str(e)}"
        ) from e


@router.post("/feedback", response_model=FeedbackResponse)
async def provide_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Provide feedback to improve the assistant's performance.
    
    Helps train the models by providing examples of successful command translations.
    """
    try:
        assistant = get_assistant()

        # Provide feedback to the assistant
        assistant.provide_feedback(
            nl_command=request.nl_command,
            executed_command=request.executed_command,
            intent=request.intent
        )

        # Try to guess intent if not provided
        intent_guessed = None
        if not request.intent:
            intent_guessed = assistant._guess_intent(request.executed_command)

        return FeedbackResponse(
            success=True,
            message="Feedback processed successfully",
            intent_guessed=intent_guessed
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process feedback: {str(e)}"
        ) from e


@router.post("/train", response_model=TrainResponse)
async def train_assistant(request: TrainRequest) -> TrainResponse:
    """
    Train or retrain the AI assistant models.
    
    Triggers training for specified components with optional force flag.
    """
    try:
        assistant = get_assistant()

        result = assistant.train_models(
            force=request.force,
            components=request.components or ["all"]
        )

        return TrainResponse(
            success=result["success"],
            message=result["message"],
            components_trained=result["components_trained"],
            before_stats=result["before_stats"],
            after_stats=result["after_stats"],
            training_time_ms=result["training_time_ms"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}"
        ) from e


@router.get("/ml_status", response_model=MLStatusResponse)
async def get_ml_status() -> MLStatusResponse:
    """
    Get the status of ML dependencies and models.
    
    Returns information about available ML libraries and model initialization status.
    """
    try:
        # Import constants to check ML availability

        assistant = get_assistant()
        status_data = assistant.status()

        return MLStatusResponse(
            sklearn_available=status_data["ml_availability"]["sklearn"],
            tensorflow_available=status_data["ml_availability"]["tensorflow"],
            models_initialized=status_data["model_details"],
            training_data_size=status_data["component_stats"]
        )

    except Exception:
        # Fallback status
        return MLStatusResponse(
            sklearn_available=False,
            tensorflow_available=False,
            models_initialized={},
            training_data_size={}
        )


@router.get("/schema", response_model=SchemaResponse)
async def get_schemas() -> SchemaResponse:
    """
    Get JSON schemas for all assistant API models.
    
    Returns comprehensive schema information for API integration.
    """
    try:
        schema_data = get_assistant_schema()

        # Create schema info metadata
        schema_info = [
            {
                "schema_name": "AssistantStatus",
                "description": "Status information for the AI assistant",
                "version": "1.0.0"
            },
            {
                "schema_name": "PredictCommandResponse",
                "description": "Response format for command predictions",
                "version": "1.0.0"
            },
            {
                "schema_name": "NLResponse",
                "description": "Response format for natural language processing",
                "version": "1.0.0"
            },
            {
                "schema_name": "CodeCompletionResponse",
                "description": "Response format for code completion",
                "version": "1.0.0"
            },
            {
                "schema_name": "TrainResponse",
                "description": "Response format for training operations",
                "version": "1.0.0"
            }
        ]

        return SchemaResponse(
            schemas=schema_data["assistant_schemas"],
            schema_info=schema_info,
            api_version="1.0.0"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schemas: {str(e)}"
        ) from e


# Health check endpoint specifically for assistant
@router.get("/health")
async def assistant_health() -> dict[str, Any]:
    """
    Health check for the assistant service.
    
    Returns basic health and readiness information.
    """
    try:
        assistant = get_assistant()
        status_data = assistant.status()

        return {
            "status": "healthy" if status_data["enabled"] else "unavailable",
            "assistant_available": ASSISTANT_AVAILABLE,
            "models_loaded": status_data["models_loaded"],
            "training_ready": status_data["training_ready"],
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "status": "error",
            "assistant_available": ASSISTANT_AVAILABLE,
            "error": str(e),
            "timestamp": time.time()
        }
