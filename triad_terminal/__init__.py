"""
Triad Terminal - Performance Instrumentation Package
Provides utilities for performance monitoring and baseline measurements.
"""

__version__ = "0.1.0"
__author__ = "Triad Terminal Team"

# Export main performance utilities
from .perf_runtime import perf_summary, record_command
from .perf_utils import get_perf_logger, time_block, timed

__all__ = [
    "timed",
    "time_block",
    "get_perf_logger",
    "record_command",
    "perf_summary",
]
