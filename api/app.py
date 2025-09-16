from __future__ import annotations

from fastapi import FastAPI

from api.routers import perf as perf_router

app = FastAPI(title="Storm OS API")

@app.get("/health")
def root_health():
    return {"ok": True}

# Mount performance router
app.include_router(perf_router.router, prefix="/perf")
