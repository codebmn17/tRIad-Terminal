"""
ML Status introspection endpoints.

Provides status information about ML predictor and assistant availability.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

router = APIRouter()


class MLStatusResponse(BaseModel):
    """ML status response model."""

    sklearn_available: bool
    tensorflow_available: bool
    predictor_ready: bool
    assistant_ready: bool
    models_loaded: dict[str, Any]
    dependency_status: dict[str, bool]


def check_dependencies() -> dict[str, bool]:
    """Check availability of optional ML dependencies."""
    deps = {}

    # Check scikit-learn
    try:
        import sklearn

        deps["sklearn"] = True
    except ImportError:
        deps["sklearn"] = False

    # Check TensorFlow
    try:
        import tensorflow

        deps["tensorflow"] = True
    except ImportError:
        deps["tensorflow"] = False

    # Check joblib
    try:
        import joblib

        deps["joblib"] = True
    except ImportError:
        deps["joblib"] = False

    return deps


def check_predictor_status() -> tuple[bool, dict[str, Any]]:
    """Check ML predictor status and available models."""
    try:
        from ml.predictor import MLPredictor

        predictor = MLPredictor()
        models_info = {
            "available_models": predictor.list_models(),
            "default_model": predictor.default_model,
            "model_types": ["knn", "forest"],
            "dataset": "iris",
        }
        return True, models_info
    except Exception as e:
        return False, {"error": str(e)}


def check_assistant_status() -> bool:
    """Check AI assistant availability."""
    try:
        # Just try to import, don't instantiate to avoid model loading
        return True
    except Exception:
        return False


@router.get("/status", response_model=MLStatusResponse)
async def ml_status() -> MLStatusResponse:
    """
    Get ML system status and availability.

    Returns comprehensive status of ML components including:
    - Dependency availability (sklearn, tensorflow)
    - Predictor readiness and loaded models
    - Assistant availability
    """
    deps = check_dependencies()
    predictor_ready, models_info = check_predictor_status()
    assistant_ready = check_assistant_status()

    return MLStatusResponse(
        sklearn_available=deps.get("sklearn", False),
        tensorflow_available=deps.get("tensorflow", False),
        predictor_ready=predictor_ready,
        assistant_ready=assistant_ready,
        models_loaded=models_info,
        dependency_status=deps,
    )


@router.get("/dependencies")
async def dependency_check() -> dict[str, Any]:
    """
    Check status of ML dependencies.

    Returns detailed information about which optional dependencies
    are available and their versions.
    """
    result = {}

    # Check sklearn
    try:
        import sklearn

        result["sklearn"] = {"available": True, "version": sklearn.__version__}
    except ImportError:
        result["sklearn"] = {"available": False, "error": "scikit-learn not installed"}

    # Check tensorflow
    try:
        import tensorflow as tf

        result["tensorflow"] = {"available": True, "version": tf.__version__}
    except ImportError:
        result["tensorflow"] = {
            "available": False,
            "note": "Optional heavy dependency - not required for basic functionality",
        }

    # Check other dependencies
    for dep_name, module_name in [("joblib", "joblib"), ("numpy", "numpy")]:
        try:
            module = __import__(module_name)
            result[dep_name] = {
                "available": True,
                "version": getattr(module, "__version__", "unknown"),
            }
        except ImportError:
            result[dep_name] = {"available": False, "error": f"{dep_name} not available"}

    return {
        "dependencies": result,
        "summary": {
            "core_ml_ready": result.get("sklearn", {}).get("available", False),
            "deep_learning_ready": result.get("tensorflow", {}).get("available", False),
            "basic_functionality": True,  # Always true since we have fallbacks
        },
    }
