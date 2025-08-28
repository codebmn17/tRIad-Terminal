"""
Performance Utilities for Triad Terminal

Provides timing decorators and context managers for performance monitoring.
Only standard library dependencies to keep it lightweight.
"""

import functools
import logging
import os
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

__all__ = ["timed", "time_block", "get_perf_logger"]

F = TypeVar("F", bound=Callable[..., Any])

def get_perf_logger() -> logging.Logger:
    """
    Get the performance logger with lazy configuration.

    Uses "triad.perf" logger name. If TRIAD_PERF environment variable
    is set (non-empty), auto-elevates to INFO level so timings show
    without changing global logging level.

    Returns:
        Configured logger for performance monitoring
    """
    logger = logging.getLogger("triad.perf")

    # Only configure if no handlers are present (lazy initialization)
    if not logger.handlers:
        # Check if we should auto-elevate to INFO level
        if os.environ.get("TRIAD_PERF"):
            logger.setLevel(logging.INFO)

            # Create simple formatter for timing logs
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # Add console handler
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            # Set to DEBUG level but don't add handlers - effectively dormant
            logger.setLevel(logging.DEBUG)

        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False

    return logger


def timed(func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """
    Decorator to log function execution time in milliseconds.

    Can be used with or without parentheses:
    @timed
    def my_function(): ...

    @timed(name="custom_name")
    def my_function(): ...

    Args:
        func: The function to wrap (when used without parentheses)
        name: Custom name for logging (defaults to function name)

    Returns:
        Decorated function that logs execution time
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_perf_logger()
            function_name = name or f.__name__

            start_time = time.perf_counter()
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                logger.info(f"[TIMING] {function_name}: {duration_ms:.2f}ms")

        return wrapper  # type: ignore

    # Handle both @timed and @timed() usage
    if func is None:
        return decorator
    else:
        return decorator(func)


@contextmanager
def time_block(name: str):
    """
    Context manager for manual scoped timing.

    Usage:
        with time_block("database_query"):
            # Your code here
            result = database.query(...)

    Args:
        name: Description of the code block being timed

    Yields:
        None
    """
    logger = get_perf_logger()
    start_time = time.perf_counter()

    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        logger.info(f"[TIMING] {name}: {duration_ms:.2f}ms")
