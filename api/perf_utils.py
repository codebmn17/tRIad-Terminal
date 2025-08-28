"""
In-process performance metrics utilities.

Collects simple duration metrics guarded by PERF_ENABLED env flag.
Default behavior: enabled if PERF_ENABLED is unset or set to "1".
"""

from __future__ import annotations

import os
import time
import threading
from typing import Callable, Any, Dict, List, Optional, TypeVar, cast

T = TypeVar("T")

# Metrics registry: metric name -> list of durations (seconds)
METRICS: Dict[str, List[float]] = {}

# Lock to protect registry mutations
_METRIC_LOCK = threading.Lock()

# PERF_ENABLED semantics:
# - If PERF_ENABLED is missing: enabled (default fast-path observability)
# - If PERF_ENABLED == "1": enabled
# - Any other value: disabled
def _is_enabled() -> bool:
    return os.getenv("PERF_ENABLED", "1") == "1"

def record(name: str, value: float) -> None:
    """
    Record a numeric value for a metric, respecting PERF_ENABLED.
    """
    if not _is_enabled():
        return
    with _METRIC_LOCK:
        METRICS.setdefault(name, []).append(value)


def timed(name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to time a function using time.monotonic() and store duration
    under the provided metric name.

    Usage:
        @timed("guess_intent")
        def _guess_intent(...):
            ...
    """
    def wrapper(func: Callable[..., T]) -> Callable[..., T]:
        def inner(*args: Any, **kwargs: Any) -> T:
            if not _is_enabled():
                return func(*args, **kwargs)
            start = time.monotonic()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.monotonic() - start
                record(name, duration)
        # Preserve minimal metadata
        inner.__name__ = getattr(func, "__name__", "timed_func")
        inner.__doc__ = getattr(func, "__doc__")
        return inner
    return wrapper


def _percentile(sorted_values: List[float], pct: float) -> Optional[float]:
    if not sorted_values:
        return None
    if pct <= 0:
        return sorted_values[0]
    if pct >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1

def snapshot() -> Dict[str, Dict[str, float]]:
    """
    Produce aggregated statistics for each metric:
        count, total, avg, p50, p95

    Returns empty dict if PERF_ENABLED is false.
    """
    if not _is_enabled():
        return {}

    with _METRIC_LOCK:
        # Copy to avoid holding lock during computation
        items = {k: v[:] for k, v in METRICS.items()}

    report: Dict[str, Dict[str, float]] = {}
    for name, values in items.items():
        if not values:
            continue
        sorted_vals = sorted(values)
        count = len(values)
        total = sum(values)
        avg = total / count
        # Percentiles
        def _pct(p: float) -> float:
            if not sorted_vals:
                return 0.0
            if p <= 0:
                return sorted_vals[0]
            if p >= 100:
                return sorted_vals[-1]
            k = (len(sorted_vals) - 1) * (p / 100.0)
            f = int(k)
            c = min(f + 1, len(sorted_vals) - 1)
            if f == c:
                return sorted_vals[f]
            d0 = sorted_vals[f] * (c - k)
            d1 = sorted_vals[c] * (k - f)
            return d0 + d1
        report[name] = {
            "count": float(count),
            "total": total,
            "avg": avg,
            "p50": _pct(50.0),
            "p95": _pct(95.0),
        }
    return report


__all__ = ["timed", "record", "snapshot", "METRICS"]
