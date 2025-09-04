"""
Enhanced Triad Terminal API with Multi-Assistant Command Center

Main FastAPI application with Storm integration, SQLite history persistence,
and dataset catalog functionality.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, ml_router
from . import ml_status, assistant
from .routers.v2 import (
    multi_assistant_router,
    history_router,
    dataset_catalog_router,
    storm_router
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Triad Terminal API",
        description="Enhanced terminal with multi-assistant command center, Storm integration, and dataset catalog",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include existing v1 routers  
    app.include_router(ml_router.router, prefix="/ml", tags=["machine-learning"])
    app.include_router(ml_status.router, prefix="/ml", tags=["ml-status"])
    app.include_router(assistant.router, prefix="/assistant", tags=["ai-assistant"])
    # Note: health router provides the old root endpoint, override with new one

    # Include new v2 API routers
    app.include_router(multi_assistant_router, prefix="/api/v2")
    app.include_router(history_router, prefix="/api/v2")
    app.include_router(dataset_catalog_router, prefix="/api/v2")
    app.include_router(storm_router, prefix="/api/v2")

    @app.get("/")
    async def root():
        """Enhanced API root endpoint."""
        return {
            "message": "Triad Terminal Multi-Assistant Command Center API",
            "version": "2.0.0",
            "features": [
                "Multi-assistant coordination",
                "Storm integration",
                "SQLite history persistence", 
                "Dataset catalog",
                "Group chat functionality",
                "Legacy ML/AI assistant support"
            ],
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "v1_legacy": "/ml, /assistant",
                "v2_enhanced": "/api/v2"
            }
        }

    @app.get("/health")
    async def enhanced_health_check():
        """Enhanced health check endpoint."""
        return {
            "status": "healthy",
            "version": "2.0.0", 
            "api_versions": ["v1", "v2"],
            "components": {
                "ml_engine": "available",
                "multi_assistant": "available",
                "storm_integration": "available",
                "history_persistence": "available",
                "dataset_catalog": "available"
            }
        }

    return app


# Create app instance
app = create_app()


def run_server():
    """Run the server (used by CLI command)."""
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)