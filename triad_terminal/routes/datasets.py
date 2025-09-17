"""Dataset management API routes."""

import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..datasets.embeddings import get_embeddings_manager
from ..datasets.ingest import get_ingestion_pipeline
from ..datasets.models import (
    BatchIngestRequest,
    DatasetRecord,
    IngestRequest,
    SearchRequest,
    SearchResponse,
)
from ..datasets.registry import get_registry_manager
from ..services.events import format_sse_event, get_event_manager

router = APIRouter()


@router.get("/list", response_model=list[DatasetRecord])
async def list_datasets(
    category: str | None = Query(None, description="Filter by category"),
    ready: bool | None = Query(None, description="Filter by ready status"),
):
    """List datasets with optional filtering."""
    registry_manager = get_registry_manager()
    datasets = registry_manager.list_datasets(category=category, ready=ready)
    return datasets


@router.get("/status/{dataset_id}", response_model=DatasetRecord)
async def get_dataset_status(dataset_id: str):
    """Get status of a specific dataset."""
    registry_manager = get_registry_manager()
    dataset = registry_manager.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    return dataset


@router.post("/ingest")
async def ingest_dataset(request: IngestRequest):
    """Start ingestion for a single dataset."""
    registry_manager = get_registry_manager()
    pipeline = get_ingestion_pipeline()

    dataset = registry_manager.get_dataset(request.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

    success = pipeline.ingest_dataset(
        request.dataset_id, force=request.force, skip_phases=request.skip_phases
    )

    if not success:
        raise HTTPException(
            status_code=409,
            detail=f"Dataset {request.dataset_id} is already being ingested or could not be started",
        )

    return {
        "message": f"Ingestion started for dataset {request.dataset_id}",
        "dataset_id": request.dataset_id,
        "force": request.force,
        "skip_phases": request.skip_phases,
    }


@router.post("/ingest/batch")
async def ingest_datasets_batch(request: BatchIngestRequest):
    """Start batch ingestion for multiple datasets."""
    pipeline = get_ingestion_pipeline()

    started = pipeline.ingest_datasets_batch(
        request.dataset_ids, force=request.force, skip_phases=request.skip_phases
    )

    return {
        "message": f"Batch ingestion started for {started}/{len(request.dataset_ids)} datasets",
        "requested": len(request.dataset_ids),
        "started": started,
        "dataset_ids": request.dataset_ids,
    }


@router.get("/stream")
async def stream_dataset_events():
    """Stream dataset events via Server-Sent Events."""
    event_manager = get_event_manager()

    async def event_stream():
        # Send initial SSE headers
        yield "retry: 10000\n"
        yield "event: connected\n"
        yield f'data: {{"type": "connected", "timestamp": "{time.time()}"}}\n\n'

        # Subscribe to datasets channel
        async for event in event_manager.subscribe("datasets"):
            yield "event: dataset-event\n"
            yield format_sse_event(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/search", response_model=SearchResponse)
async def search_datasets(request: SearchRequest):
    """Search datasets using embeddings (if enabled)."""
    embeddings_manager = get_embeddings_manager()

    if not embeddings_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Embeddings are not enabled. Set ENABLE_EMBEDDINGS=1 and ensure fastembed is installed.",
        )

    start_time = time.time()

    # Perform search
    if request.dataset_ids:
        results = embeddings_manager.search_multiple_datasets(
            request.dataset_ids, request.query, request.limit, request.threshold
        )
    else:
        results = embeddings_manager.search_all_ready_datasets(
            request.query, request.limit, request.threshold
        )

    took_ms = (time.time() - start_time) * 1000

    return SearchResponse(results=results, query=request.query, total=len(results), took_ms=took_ms)


@router.get("/embeddings/status")
async def get_embeddings_status():
    """Get embeddings system status."""
    embeddings_manager = get_embeddings_manager()

    return {
        "enabled": embeddings_manager.is_available(),
        "backend": embeddings_manager.backend,
        "model": embeddings_manager.model_name,
        "max_chunk_tokens": embeddings_manager.max_chunk_tokens,
    }
