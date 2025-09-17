"""Startup integration for dataset system."""

import asyncio

from .config_datasets import AUTO_DOWNLOAD_DATASETS, INITIAL_DATASETS
from .datasets.ingest import get_ingestion_pipeline
from .datasets.registry import get_registry_manager


async def initialize_dataset_system():
    """Initialize the dataset system on startup."""
    print("Initializing dataset system...")

    # Load registry
    registry_manager = get_registry_manager()
    datasets = registry_manager.list_datasets()
    print(f"Loaded {len(datasets)} datasets from registry")

    # Auto-download initial datasets if enabled
    if AUTO_DOWNLOAD_DATASETS and INITIAL_DATASETS:
        print(f"Auto-download enabled, starting ingestion for: {', '.join(INITIAL_DATASETS)}")

        pipeline = get_ingestion_pipeline()
        started = pipeline.ingest_datasets_batch(INITIAL_DATASETS, force=False)

        if started > 0:
            print(f"Started ingestion for {started}/{len(INITIAL_DATASETS)} datasets")
        else:
            print("No datasets were started (may already be completed or in progress)")

    print("Dataset system initialization complete")


def startup_datasets_sync():
    """Synchronous wrapper for startup initialization."""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the task
            asyncio.create_task(initialize_dataset_system())
        else:
            # Run in the existing loop
            loop.run_until_complete(initialize_dataset_system())
    except RuntimeError:
        # No event loop exists, create one
        asyncio.run(initialize_dataset_system())
