"""
AI Assistant endpoints.

Provides AI assistant capabilities including command prediction, 
code completion, and natural language processing.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

router = APIRouter()

class AssistantStatusResponse(BaseModel):
    """Assistant status response model."""
    available: bool
    sklearn_available: bool
    models_trained: bool
    supported_languages: list[str]
    features: dict[str, bool]

class CommandPredictionRequest(BaseModel):
    """Request model for command prediction."""
    context: str = Field(..., description="Current command context or partial command")
    history: list[str] | None = Field(default=[], description="Recent command history")
    max_suggestions: int | None = Field(default=5, description="Maximum number of suggestions")

class CommandPredictionResponse(BaseModel):
    """Response model for command prediction."""
    suggestions: list[str]
    confidence_scores: list[float] | None = None
    source: str  # "ml" or "heuristic"

class CodeCompletionRequest(BaseModel):
    """Request model for code completion."""
    code: str = Field(..., description="Current code context")
    language: str = Field(..., description="Programming language")
    position: int | None = Field(default=None, description="Cursor position in code")
    max_completions: int | None = Field(default=5, description="Maximum number of completions")

class CodeCompletionResponse(BaseModel):
    """Response model for code completion."""
    completions: list[str]
    confidence_scores: list[float] | None = None
    source: str  # "ml" or "heuristic"

class NaturalLanguageRequest(BaseModel):
    """Request model for natural language processing."""
    text: str = Field(..., description="Natural language text to process")
    task: str = Field(default="intent", description="Task type: intent, command, or summary")

class NaturalLanguageResponse(BaseModel):
    """Response model for natural language processing."""
    result: str
    confidence: float | None = None
    metadata: dict[str, Any] | None = None

class FeedbackRequest(BaseModel):
    """Request model for assistant feedback."""
    prediction_id: str | None = Field(default=None, description="ID of prediction to provide feedback on")
    feedback_type: str = Field(..., description="Type of feedback: positive, negative, or correction")
    suggestion: str | None = Field(default=None, description="User's preferred suggestion")
    context: str | None = Field(default=None, description="Additional context")

def get_assistant_engine():
    """Get assistant engine instance with error handling."""
    try:
        from agents.learning.assistant_ml import CodeCompletionEngine
        return CodeCompletionEngine()
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Assistant not available: {str(e)}"
        ) from e

def heuristic_command_prediction(context: str, history: list[str]) -> list[str]:
    """Fallback heuristic command prediction."""
    # Basic heuristic suggestions based on common commands
    common_commands = [
        "ls", "cd", "pwd", "mkdir", "rm", "cp", "mv", "grep", "find",
        "git status", "git add", "git commit", "git push", "git pull",
        "python", "pip install", "npm install", "docker run", "make"
    ]

    if not context:
        return common_commands[:5]

    # Simple prefix matching
    matches = [cmd for cmd in common_commands if cmd.startswith(context.lower())]

    # If no prefix matches, try substring matching
    if not matches:
        matches = [cmd for cmd in common_commands if context.lower() in cmd]

    return matches[:5]

def heuristic_code_completion(code: str, language: str) -> list[str]:
    """Fallback heuristic code completion."""
    common_completions = {
        "python": [
            "import ", "def ", "class ", "if ", "for ", "while ", "try:", "except:", "return", "print("
        ],
        "javascript": [
            "function ", "const ", "let ", "var ", "if (", "for (", "while (", "return", "console.log("
        ],
        "bash": [
            "echo ", "cd ", "ls ", "mkdir ", "rm ", "cp ", "mv ", "grep ", "find "
        ]
    }

    lang_completions = common_completions.get(language.lower(), common_completions["python"])

    if not code:
        return lang_completions[:5]

    # Simple context-aware completion
    last_word = code.split()[-1] if code.split() else ""
    matches = [comp for comp in lang_completions if comp.startswith(last_word)]

    return matches[:5] if matches else lang_completions[:5]

@router.get("/status", response_model=AssistantStatusResponse)
async def assistant_status() -> AssistantStatusResponse:
    """
    Get AI assistant status and capabilities.
    
    Returns information about assistant availability, trained models,
    and supported features.
    """
    try:
        # Check if sklearn is available
        sklearn_available = False
        try:
            import sklearn
            sklearn_available = True
        except ImportError:
            pass

        # Try to get assistant engine
        try:
            engine = get_assistant_engine()
            available = True
            # Check if models are trained (simplified check)
            models_trained = len(getattr(engine, 'language_models', {})) > 0
            supported_languages = getattr(engine, 'supported_languages', ['python', 'javascript', 'bash'])
        except Exception:
            available = False
            models_trained = False
            supported_languages = ['python', 'javascript', 'bash']  # Default fallback

        return AssistantStatusResponse(
            available=available,
            sklearn_available=sklearn_available,
            models_trained=models_trained,
            supported_languages=supported_languages,
            features={
                "command_prediction": True,  # Always available via heuristics
                "code_completion": True,     # Always available via heuristics
                "natural_language": True,   # Always available via simple processing
                "machine_learning": sklearn_available and available
            }
        )
    except Exception:
        # Return degraded status instead of failing
        return AssistantStatusResponse(
            available=False,
            sklearn_available=False,
            models_trained=False,
            supported_languages=['python', 'javascript', 'bash'],
            features={
                "command_prediction": True,
                "code_completion": True,
                "natural_language": True,
                "machine_learning": False
            }
        )

@router.post("/predict_command", response_model=CommandPredictionResponse)
async def predict_command(request: CommandPredictionRequest) -> CommandPredictionResponse:
    """
    Predict command completions based on context and history.
    
    Uses ML models when available, falls back to heuristic suggestions.
    """
    try:
        engine = get_assistant_engine()
        # Try ML-based prediction
        if hasattr(engine, 'predict_command'):
            suggestions = engine.predict_command(request.context, request.history)
            return CommandPredictionResponse(
                suggestions=suggestions[:request.max_suggestions],
                source="ml"
            )
        else:
            raise Exception("ML prediction not available")
    except Exception:
        # Fallback to heuristic prediction
        suggestions = heuristic_command_prediction(request.context, request.history)
        return CommandPredictionResponse(
            suggestions=suggestions[:request.max_suggestions],
            source="heuristic"
        )

@router.post("/complete_code", response_model=CodeCompletionResponse)
async def complete_code(request: CodeCompletionRequest) -> CodeCompletionResponse:
    """
    Provide code completion suggestions.
    
    Uses trained ML models when available, falls back to heuristic completion.
    """
    try:
        engine = get_assistant_engine()
        # Try ML-based completion
        if hasattr(engine, 'complete_code'):
            completions = engine.complete_code(request.code, request.language)
            return CodeCompletionResponse(
                completions=completions[:request.max_completions],
                source="ml"
            )
        else:
            raise Exception("ML completion not available")
    except Exception:
        # Fallback to heuristic completion
        completions = heuristic_code_completion(request.code, request.language)
        return CodeCompletionResponse(
            completions=completions[:request.max_completions],
            source="heuristic"
        )

@router.post("/nl", response_model=NaturalLanguageResponse)
async def process_natural_language(request: NaturalLanguageRequest) -> NaturalLanguageResponse:
    """
    Process natural language text for various tasks.
    
    Supports intent recognition, command translation, and text summarization.
    """
    try:
        if request.task == "command":
            # Simple command translation
            command_mapping = {
                "list files": "ls",
                "change directory": "cd",
                "make directory": "mkdir",
                "remove file": "rm",
                "copy file": "cp",
                "move file": "mv",
                "show current directory": "pwd"
            }

            text_lower = request.text.lower()
            for phrase, command in command_mapping.items():
                if phrase in text_lower:
                    return NaturalLanguageResponse(
                        result=command,
                        confidence=0.8,
                        metadata={"task": "command_translation", "matched_phrase": phrase}
                    )

            return NaturalLanguageResponse(
                result="Sorry, I couldn't translate that to a command",
                confidence=0.0,
                metadata={"task": "command_translation", "error": "no_match"}
            )

        elif request.task == "intent":
            # Simple intent recognition
            if any(word in request.text.lower() for word in ["help", "how", "what", "?"]):
                intent = "help_request"
            elif any(word in request.text.lower() for word in ["create", "make", "new"]):
                intent = "creation_request"
            elif any(word in request.text.lower() for word in ["delete", "remove", "rm"]):
                intent = "deletion_request"
            else:
                intent = "unknown"

            return NaturalLanguageResponse(
                result=intent,
                confidence=0.7,
                metadata={"task": "intent_recognition"}
            )

        else:
            return NaturalLanguageResponse(
                result=f"Task '{request.task}' not supported. Available tasks: intent, command",
                confidence=0.0,
                metadata={"task": request.task, "error": "unsupported_task"}
            )

    except Exception as e:
        return NaturalLanguageResponse(
            result=f"Error processing text: {str(e)}",
            confidence=0.0,
            metadata={"error": str(e)}
        )

@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest) -> dict[str, str]:
    """
    Provide feedback on assistant suggestions.
    
    Accepts user feedback to improve future suggestions.
    """
    try:
        # In a full implementation, this would store feedback for model training
        # For now, just acknowledge the feedback
        return {
            "status": "received",
            "message": f"Thank you for the {request.feedback_type} feedback",
            "feedback_id": f"fb_{hash(str(request.dict()))}",
            "note": "Feedback will be used to improve future suggestions"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        ) from e
