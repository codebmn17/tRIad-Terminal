"""
Main FastAPI application for tRIad Terminal.

This module creates the production-ready FastAPI application with proper
structure and endpoints. It includes health checks and ML prediction routes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, ml_router

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="tRIad Terminal API",
        description="Production-ready API for machine learning and system operations",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(ml_router.router, prefix="/ml", tags=["machine-learning"])

    return app

# Create app instance
app = create_app()