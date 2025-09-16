from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from api.perf_utils import record, snapshot

router = APIRouter()


@router.get("/health")
def perf_health() -> dict[str, bool]:
    return {"ok": True}


@router.get("/status")
def perf_status() -> dict[str, Any]:
    # Expose enabled flag implicitly via presence/absence of metrics.
    metrics = snapshot()
    return {
        "metrics": metrics,
        "metrics_count": len(metrics),
    }


@router.post("/mark")
def perf_mark(
    name: str = Body(..., embed=True),
    meta: dict[str, Any] | None = Body(default=None),
) -> dict[str, Any]:
    # Duration-free event; record zero so it contributes to count.
    record(name, 0.0)
    return {"recorded": True, "name": name, "meta": meta}
