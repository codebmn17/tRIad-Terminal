"""Dataset models for tRIad Terminal."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PhaseStatus(str, Enum):
    """Dataset ingestion phase status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


class DatasetPhases(BaseModel):
    """Dataset ingestion phases tracking."""

    download: PhaseStatus = PhaseStatus.PENDING
    normalize: PhaseStatus = PhaseStatus.PENDING
    embed: PhaseStatus = PhaseStatus.PENDING


class DatasetMetadata(BaseModel):
    """Dataset metadata."""

    language: str | None = None
    task: str | None = None
    license: str | None = None
    document_types: list[str] | None = None
    extra: dict[str, Any] | None = None


class DatasetRecord(BaseModel):
    """Dataset record model."""

    id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Human-readable dataset name")
    category: str = Field(..., description="Dataset category (coding, history, finance, etc.)")
    description: str = Field(..., description="Dataset description")
    source_url: str | None = Field(None, description="Original data source URL")
    sample_size: int | None = Field(None, description="Number of samples")
    format: str = Field(default="jsonl", description="Data format")
    metadata: DatasetMetadata = Field(default_factory=DatasetMetadata)
    phases: DatasetPhases = Field(default_factory=DatasetPhases)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Runtime fields
    ready: bool = Field(default=False, description="True if all phases completed successfully")
    error_message: str | None = Field(None, description="Latest error message if any")
    progress: dict[str, Any] | None = Field(None, description="Phase-specific progress info")

    def is_phase_completed(self, phase: str) -> bool:
        """Check if a specific phase is completed."""
        phase_status = getattr(self.phases, phase, None)
        return phase_status == PhaseStatus.COMPLETED

    def update_phase_status(self, phase: str, status: PhaseStatus) -> None:
        """Update phase status."""
        if hasattr(self.phases, phase):
            setattr(self.phases, phase, status)
            self.updated_at = datetime.utcnow()

            # Update ready status
            all_phases = [self.phases.download, self.phases.normalize, self.phases.embed]
            self.ready = all(s in [PhaseStatus.COMPLETED, PhaseStatus.SKIPPED] for s in all_phases)


class DatasetRegistry(BaseModel):
    """Dataset registry containing all datasets."""

    datasets: list[DatasetRecord] = Field(default_factory=list)
    version: str = Field(default="1.0.0")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        """Get dataset by ID."""
        for dataset in self.datasets:
            if dataset.id == dataset_id:
                return dataset
        return None

    def add_dataset(self, dataset: DatasetRecord) -> None:
        """Add or update dataset."""
        existing = self.get_dataset(dataset.id)
        if existing:
            # Update existing
            for i, d in enumerate(self.datasets):
                if d.id == dataset.id:
                    self.datasets[i] = dataset
                    break
        else:
            # Add new
            self.datasets.append(dataset)

        self.last_updated = datetime.utcnow()

    def filter_datasets(
        self, category: str | None = None, ready: bool | None = None
    ) -> list[DatasetRecord]:
        """Filter datasets by criteria."""
        filtered = self.datasets

        if category:
            filtered = [d for d in filtered if d.category == category]

        if ready is not None:
            filtered = [d for d in filtered if d.ready == ready]

        return filtered


class IngestRequest(BaseModel):
    """Dataset ingestion request."""

    dataset_id: str = Field(..., description="Dataset ID to ingest")
    force: bool = Field(default=False, description="Force re-ingestion if already completed")
    skip_phases: list[str] = Field(default_factory=list, description="Phases to skip")


class BatchIngestRequest(BaseModel):
    """Batch dataset ingestion request."""

    dataset_ids: list[str] = Field(..., description="Dataset IDs to ingest")
    force: bool = Field(default=False, description="Force re-ingestion if already completed")
    skip_phases: list[str] = Field(default_factory=list, description="Phases to skip")


class SearchRequest(BaseModel):
    """Dataset search request."""

    query: str = Field(..., description="Search query")
    dataset_ids: list[str] | None = Field(None, description="Datasets to search in")
    limit: int = Field(default=10, description="Maximum number of results")
    threshold: float = Field(default=0.7, description="Minimum similarity threshold")


class SearchResult(BaseModel):
    """Search result item."""

    dataset_id: str
    content: str
    score: float
    metadata: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    """Search response."""

    results: list[SearchResult]
    query: str
    total: int
    took_ms: float
