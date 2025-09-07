"""
Main FastAPI application for tRIad Terminal.

This module creates the production-ready FastAPI application with proper
structure and endpoints. It includes health checks and ML prediction routes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import ml_status
from .routers import assistant, health, ml_router

# Import dataset routes
try:
    from triad_terminal.routes.datasets import router as datasets_router

    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="tRIad Terminal API",
        description="Production-ready API for machine learning and system operations",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
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
    app.include_router(ml_status.router, prefix="/ml", tags=["ml-status"])
    app.include_router(assistant.router, prefix="/assistant", tags=["ai-assistant"])

    # Include datasets router if available
    if DATASETS_AVAILABLE:
        app.include_router(datasets_router, prefix="/datasets", tags=["datasets"])

    # Mount static files
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # Static directory doesn't exist, ignore
        pass

    # Add template serving route
    @app.get("/datasets")
    async def serve_datasets_panel():
        """Serve the datasets management panel."""
        try:
            return FileResponse("templates/datasets_panel.html")
        except FileNotFoundError:
            return {"error": "Dashboard not available"}

    return app


# Create app instance
app = create_app()


# Initialize dataset system on startup
if DATASETS_AVAILABLE:
    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize systems on startup."""
        try:
            from triad_terminal.startup_datasets import initialize_dataset_system

            await initialize_dataset_system()
        except Exception as e:  # noqa: BLE001
            # Log and continue to avoid crashing the app on optional feature init
            print(f"Error initializing dataset system: {e}")
