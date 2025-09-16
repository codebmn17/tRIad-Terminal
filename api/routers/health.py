"""
Health check endpoints.

Provides system health and status information.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    service: str
    version: str

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the current health status of the API service.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="tRIad-Terminal-API",
        version="1.0.0"
    )

@router.get("/")
async def root() -> dict[str, Any]:
    """
    Root endpoint with basic API information.
    
    Returns basic information about the API and available endpoints.
    """
    return {
        "message": "tRIad Terminal API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ml_predict": "/ml/predict",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
