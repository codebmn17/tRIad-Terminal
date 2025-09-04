"""
Multi-Assistant Command Center API v2

Enhanced endpoints for multi-assistant coordination, history persistence,
and dataset catalog functionality.
"""

from .multi_assistant import router as multi_assistant_router
from .history import router as history_router
from .dataset_catalog import router as dataset_catalog_router
from .storm import router as storm_router

__all__ = [
    "multi_assistant_router",
    "history_router", 
    "dataset_catalog_router",
    "storm_router",
]