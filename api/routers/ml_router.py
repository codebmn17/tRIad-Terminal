"""
Machine Learning prediction endpoints.

Provides ML model prediction capabilities.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ml.predictor import MLPredictor

router = APIRouter()

# Initialize the ML predictor
predictor = MLPredictor()

class PredictionRequest(BaseModel):
    """Request model for ML predictions."""
    features: List[float] = Field(..., description="Input features for prediction")
    model_type: Optional[str] = Field("auto", description="Model type to use (auto, knn, forest)")

    @validator("features")
    def validate_features(cls, v):
        """Validate that features is a non-empty list of numbers."""
        if not v:
            raise ValueError("features cannot be empty")
        try:
            [float(x) for x in v]
        except (TypeError, ValueError) as e:
            raise ValueError("All features must be numeric") from e
        return v

class PredictionResponse(BaseModel):
    """Response model for ML predictions."""
    prediction: Any
    model_used: str
    confidence: Optional[float] = None
    processing_time_ms: float

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Make predictions using ML models.
    
    This is a stub endpoint that can be easily replaced with real ML logic.
    Currently supports basic classification on numeric features.
    """
    try:
        result = predictor.predict(
            features=request.features,
            model_type=request.model_type
        )
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Prediction failed: {str(e)}"
        ) from e

@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """
    List available ML models.
    
    Returns information about available models and their capabilities.
    """
    return {
        "available_models": predictor.list_models(),
        "default_model": predictor.default_model,
        "model_info": {
            "input_format": "List of numeric features",
            "supported_types": ["classification", "regression"],
            "frameworks": ["scikit-learn"]
        }
    }