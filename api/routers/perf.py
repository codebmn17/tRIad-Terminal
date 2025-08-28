from __future__ import annotations

from fastapi import APIRouter, Body
from typing import Any, Dict, Optional

from api.perf_utils import record, snapshot

router = APIRouter()

@router.get("/health")
def perf_health() -> Dict[str, bool]:
    return {"ok": True}

@router.get("/status")
def perf_status() -> Dict[str, Any]:
    # Expose enabled flag implicitly via presence/absence of metrics.
    metrics = snapshot()
    return {
        "metrics": metrics,
        "metrics_count": len(metrics),
    }

@router.post("/mark")
def perf_mark(
    name: str = Body(..., embed=True),
    meta: Optional[Dict[str, Any]] = Body(default=None),
) -> Dict[str, Any]:
    # Duration-free event; record zero so it contributes to count.
    record(name, 0.0)
    return {"recorded": True, "name": name, "meta": meta}
