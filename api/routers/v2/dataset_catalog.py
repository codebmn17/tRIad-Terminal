"""
Dataset Catalog API

FastAPI endpoints for managing and accessing the dataset catalog.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from triad.services import DatasetCatalogService


router = APIRouter(prefix="/datasets", tags=["Dataset Catalog"])

# Service instance
catalog_service = DatasetCatalogService()


class DatasetCreateRequest(BaseModel):
    """Request to create a new dataset entry."""
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Dataset description")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    source_url: Optional[str] = Field(None, description="Original source URL")
    version: str = Field(default="1.0", description="Dataset version")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DatasetResponse(BaseModel):
    """Response containing dataset information."""
    id: str
    name: str
    description: Optional[str]
    type: str
    size_bytes: int
    rows: Optional[int]
    columns: Optional[int]
    schema_info: Dict[str, Any]
    tags: List[str]
    source_url: Optional[str]
    version: str
    created_at: str
    updated_at: str
    last_accessed: Optional[str]
    access_count: int
    metadata: Dict[str, Any]


class DatasetListResponse(BaseModel):
    """Response for dataset listing."""
    datasets: List[DatasetResponse]
    total_count: int
    limit: int
    offset: int
    filters: Dict[str, Any]


class DatasetUsageStatsResponse(BaseModel):
    """Response for dataset usage statistics."""
    dataset_id: str
    total_usage_count: int
    operations: Dict[str, int]
    recent_usage: List[Dict[str, Any]]


class CatalogStatsResponse(BaseModel):
    """Response for catalog statistics."""
    total_datasets: int
    datasets_by_type: Dict[str, int]
    total_size_bytes: int
    popular_datasets: List[Dict[str, Any]]


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_id: str = Query(..., description="Unique identifier for the dataset"),
    name: str = Query(..., description="Human-readable name"),
    description: Optional[str] = Query(None, description="Dataset description"),
    tags: str = Query("", description="Comma-separated tags"),
    source_url: Optional[str] = Query(None, description="Original source URL"),
    version: str = Query("1.0", description="Dataset version")
) -> DatasetResponse:
    """Upload and register a new dataset file."""
    try:
        # Save uploaded file to temporary location
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Add dataset to catalog
        dataset_info = await catalog_service.add_dataset(
            dataset_id=dataset_id,
            name=name,
            file_path=temp_path,
            description=description,
            tags=tag_list,
            source_url=source_url,
            version=version,
            copy_file=True
        )
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        return DatasetResponse(**dataset_info)
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")


@router.post("", response_model=DatasetResponse)
async def create_dataset_from_path(request: DatasetCreateRequest, file_path: str) -> DatasetResponse:
    """Register an existing dataset file by path."""
    try:
        dataset_info = await catalog_service.add_dataset(
            dataset_id=request.dataset_id,
            name=request.name,
            file_path=file_path,
            description=request.description,
            tags=request.tags,
            source_url=request.source_url,
            version=request.version,
            metadata=request.metadata,
            copy_file=False  # Don't copy, just reference
        )
        
        return DatasetResponse(**dataset_info)
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    dataset_type: Optional[str] = Query(None, description="Filter by dataset type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of datasets to return"),
    offset: int = Query(0, ge=0, description="Number of datasets to skip")
) -> DatasetListResponse:
    """List datasets with optional filtering."""
    try:
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None
        
        datasets = await catalog_service.list_datasets(
            dataset_type=dataset_type,
            tags=tag_list,
            limit=limit,
            offset=offset
        )
        
        filters = {}
        if dataset_type:
            filters["dataset_type"] = dataset_type
        if tag_list:
            filters["tags"] = tag_list
        
        return DatasetListResponse(
            datasets=[DatasetResponse(**ds) for ds in datasets],
            total_count=len(datasets),
            limit=limit,
            offset=offset,
            filters=filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


@router.get("/search", response_model=DatasetListResponse)
async def search_datasets(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
) -> DatasetListResponse:
    """Search datasets by name, description, or tags."""
    try:
        datasets = await catalog_service.search_datasets(query=q, limit=limit)
        
        return DatasetListResponse(
            datasets=[DatasetResponse(**ds) for ds in datasets],
            total_count=len(datasets),
            limit=limit,
            offset=0,
            filters={"search_query": q}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search datasets: {str(e)}")


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str) -> DatasetResponse:
    """Get detailed information about a specific dataset."""
    try:
        dataset = await catalog_service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return DatasetResponse(**dataset)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(dataset_id: str, updates: Dict[str, Any]) -> DatasetResponse:
    """Update dataset information."""
    try:
        success = await catalog_service.update_dataset(dataset_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Dataset not found or no valid updates provided")
        
        # Return updated dataset
        updated_dataset = await catalog_service.get_dataset(dataset_id)
        return DatasetResponse(**updated_dataset)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update dataset: {str(e)}")


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    remove_file: bool = Query(True, description="Whether to remove the dataset file")
) -> Dict[str, str]:
    """Delete a dataset from the catalog."""
    try:
        success = await catalog_service.delete_dataset(dataset_id, remove_file=remove_file)
        
        if not success:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return {
            "status": "deleted",
            "dataset_id": dataset_id,
            "file_removed": remove_file
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")


@router.post("/{dataset_id}/usage")
async def log_dataset_usage(
    dataset_id: str,
    operation: str = Query(..., description="Operation performed on dataset"),
    assistant_type: Optional[str] = Query(None, description="Type of assistant using dataset"),
    session_id: Optional[str] = Query(None, description="Session ID if applicable"),
    rows_processed: Optional[int] = Query(None, description="Number of rows processed"),
    processing_time_ms: Optional[int] = Query(None, description="Processing time in milliseconds"),
    success: bool = Query(True, description="Whether operation was successful"),
    error_message: Optional[str] = Query(None, description="Error message if operation failed")
) -> Dict[str, Any]:
    """Log usage of a dataset."""
    try:
        usage_id = await catalog_service.log_dataset_usage(
            dataset_id=dataset_id,
            operation=operation,
            assistant_type=assistant_type,
            session_id=session_id,
            rows_processed=rows_processed,
            processing_time_ms=processing_time_ms,
            success=success,
            error_message=error_message
        )
        
        return {
            "status": "logged",
            "usage_id": usage_id,
            "dataset_id": dataset_id,
            "operation": operation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log dataset usage: {str(e)}")


@router.get("/{dataset_id}/usage", response_model=DatasetUsageStatsResponse)
async def get_dataset_usage_stats(dataset_id: str) -> DatasetUsageStatsResponse:
    """Get usage statistics for a dataset."""
    try:
        # Check if dataset exists
        dataset = await catalog_service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        stats = await catalog_service.get_dataset_usage_stats(dataset_id)
        
        return DatasetUsageStatsResponse(
            dataset_id=dataset_id,
            **stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage stats: {str(e)}")


@router.get("/", response_model=CatalogStatsResponse)
async def get_catalog_stats() -> CatalogStatsResponse:
    """Get overall catalog statistics."""
    try:
        stats = await catalog_service.get_catalog_stats()
        
        return CatalogStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get catalog stats: {str(e)}")


@router.get("/{dataset_id}/download")
async def download_dataset(dataset_id: str):
    """Download a dataset file."""
    try:
        dataset = await catalog_service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # In a real implementation, this would stream the file
        # For now, just return the file path info
        return {
            "dataset_id": dataset_id,
            "name": dataset["name"],
            "path": dataset["path"],
            "size_bytes": dataset["size_bytes"],
            "message": "File download not implemented - path provided for reference"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download dataset: {str(e)}")