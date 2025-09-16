"""Dataset ingestion pipeline."""

import json
import threading
import time
import uuid
from datetime import datetime
from typing import Any

from ..services.events import get_event_manager
from .models import DatasetRecord, PhaseStatus
from .registry import get_registry_manager


class IngestionPhase:
    """Base class for ingestion phases."""

    def __init__(self, name: str):
        self.name = name

    def should_run(self, dataset: DatasetRecord, force: bool = False, skip_phases: list[str] | None = None) -> bool:
        """Check if phase should run."""
        if skip_phases and self.name in skip_phases:
            return False

        if force:
            return True

        phase_status = getattr(dataset.phases, self.name, PhaseStatus.PENDING)
        return phase_status not in [PhaseStatus.COMPLETED, PhaseStatus.RUNNING]

    def execute(self, dataset: DatasetRecord, context: dict[str, Any]) -> bool:
        """Execute the phase. Return True if successful."""
        raise NotImplementedError


class DownloadPhase(IngestionPhase):
    """Download phase - stub implementation."""

    def __init__(self):
        super().__init__("download")

    def execute(self, dataset: DatasetRecord, context: dict[str, Any]) -> bool:
        """Simulate downloading data."""
        registry_manager = get_registry_manager()
        dataset_path = registry_manager.get_dataset_path(dataset.id)
        raw_path = dataset_path / "raw"
        raw_path.mkdir(parents=True, exist_ok=True)

        # Simulate download with sample data based on category
        sample_data = self._generate_sample_data(dataset)

        raw_file = raw_path / "data.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)

        context['raw_file'] = raw_file
        return True

    def _generate_sample_data(self, dataset: DatasetRecord) -> list[dict[str, Any]]:
        """Generate sample data based on dataset category."""
        if dataset.category == "coding":
            return [
                {"id": f"code_{i}", "code": f"def function_{i}():\n    return {i}", "docstring": f"Function that returns {i}"}
                for i in range(min(dataset.sample_size or 10, 10))
            ]
        elif dataset.category == "history":
            return [
                {"id": f"event_{i}", "title": f"Historical Event {i}", "description": f"Description of historical event {i}", "date": f"2024-01-{i+1:02d}"}
                for i in range(min(dataset.sample_size or 10, 10))
            ]
        elif dataset.category == "finance":
            return [
                {"id": f"filing_{i}", "company": f"Company {i}", "document_type": "10-K", "content": f"Financial filing content {i}"}
                for i in range(min(dataset.sample_size or 10, 10))
            ]
        else:
            return [
                {"id": f"item_{i}", "content": f"Sample content {i}"}
                for i in range(min(dataset.sample_size or 10, 10))
            ]


class NormalizePhase(IngestionPhase):
    """Normalize phase - convert to JSONL format."""

    def __init__(self):
        super().__init__("normalize")

    def execute(self, dataset: DatasetRecord, context: dict[str, Any]) -> bool:
        """Normalize data to JSONL format."""
        registry_manager = get_registry_manager()

        # Get input file
        raw_file = context.get('raw_file')
        if not raw_file:
            dataset_path = registry_manager.get_dataset_path(dataset.id)
            raw_file = dataset_path / "raw" / "data.json"

        if not raw_file.exists():
            return False

        # Create normalized directory
        normalized_path = registry_manager.get_dataset_path(dataset.id) / "normalized"
        normalized_path.mkdir(parents=True, exist_ok=True)

        # Load and normalize data
        with open(raw_file, encoding='utf-8') as f:
            raw_data = json.load(f)

        # Write as JSONL
        output_file = normalized_path / "data.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in raw_data:
                # Ensure each item has required fields
                normalized_item = {
                    "id": item.get("id", str(uuid.uuid4())),
                    "text": self._extract_text(item),
                    "metadata": {k: v for k, v in item.items() if k not in ["id", "text"]}
                }
                f.write(json.dumps(normalized_item, ensure_ascii=False) + '\n')

        context['normalized_file'] = output_file
        return True

    def _extract_text(self, item: dict[str, Any]) -> str:
        """Extract main text content from item."""
        # Priority order for text extraction
        text_fields = ["text", "content", "description", "code", "docstring", "title"]

        for field in text_fields:
            if field in item and item[field]:
                return str(item[field])

        # Fallback to string representation
        return str(item)


class EmbedPhase(IngestionPhase):
    """Embedding phase - generate vectors (optional)."""

    def __init__(self):
        super().__init__("embed")

    def should_run(self, dataset: DatasetRecord, force: bool = False, skip_phases: list[str] | None = None) -> bool:
        """Check if embeddings are enabled."""
        import os
        if not os.environ.get("ENABLE_EMBEDDINGS"):
            return False
        return super().should_run(dataset, force, skip_phases)

    def execute(self, dataset: DatasetRecord, context: dict[str, Any]) -> bool:
        """Generate embeddings for normalized data."""
        try:
            from .embeddings import EmbeddingsManager
        except ImportError:
            print("Embeddings dependencies not available, skipping embed phase")
            return False

        registry_manager = get_registry_manager()

        # Get normalized data
        normalized_file = context.get('normalized_file')
        if not normalized_file:
            normalized_file = registry_manager.get_normalized_data_path(dataset.id)

        if not normalized_file.exists():
            return False

        # Create embeddings
        embeddings_manager = EmbeddingsManager()
        success = embeddings_manager.create_embeddings_for_dataset(dataset.id, normalized_file)

        return success


class IngestionPipeline:
    """Main ingestion pipeline orchestrator."""

    def __init__(self):
        self.phases = [
            DownloadPhase(),
            NormalizePhase(),
            EmbedPhase()
        ]
        self.registry_manager = get_registry_manager()
        self.event_manager = get_event_manager()

        # Track running ingestions
        self._running_ingestions: dict[str, threading.Thread] = {}

    def ingest_dataset(self, dataset_id: str, force: bool = False, skip_phases: list[str] | None = None) -> bool:
        """Start dataset ingestion in background thread."""
        if dataset_id in self._running_ingestions:
            print(f"Dataset {dataset_id} is already being ingested")
            return False

        dataset = self.registry_manager.get_dataset(dataset_id)
        if not dataset:
            print(f"Dataset {dataset_id} not found")
            return False

        # Start ingestion thread
        thread = threading.Thread(
            target=self._ingest_dataset_thread,
            args=(dataset, force, skip_phases),
            daemon=True
        )

        self._running_ingestions[dataset_id] = thread
        thread.start()
        return True

    def ingest_datasets_batch(self, dataset_ids: list[str], force: bool = False, skip_phases: list[str] | None = None) -> int:
        """Start batch ingestion."""
        started = 0
        for dataset_id in dataset_ids:
            if self.ingest_dataset(dataset_id, force, skip_phases):
                started += 1
        return started

    def _ingest_dataset_thread(self, dataset: DatasetRecord, force: bool = False, skip_phases: list[str] | None = None):
        """Run ingestion in thread."""
        try:
            self._publish_event("ingestion_started", {
                "dataset_id": dataset.id,
                "timestamp": datetime.utcnow().isoformat()
            })

            context: dict[str, Any] = {}

            for phase in self.phases:
                if not phase.should_run(dataset, force, skip_phases):
                    dataset.update_phase_status(phase.name, PhaseStatus.SKIPPED)
                    continue

                # Update phase to running
                dataset.update_phase_status(phase.name, PhaseStatus.RUNNING)
                self.registry_manager.update_dataset(dataset)

                self._publish_event("phase_started", {
                    "dataset_id": dataset.id,
                    "phase": phase.name,
                    "timestamp": datetime.utcnow().isoformat()
                })

                try:
                    # Simulate some processing time
                    time.sleep(1)  # Remove in production or make configurable

                    success = phase.execute(dataset, context)

                    if success:
                        dataset.update_phase_status(phase.name, PhaseStatus.COMPLETED)
                        self._publish_event("phase_completed", {
                            "dataset_id": dataset.id,
                            "phase": phase.name,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        dataset.update_phase_status(phase.name, PhaseStatus.ERROR)
                        dataset.error_message = f"Phase {phase.name} failed"
                        self._publish_event("phase_error", {
                            "dataset_id": dataset.id,
                            "phase": phase.name,
                            "error": f"Phase {phase.name} failed",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        break

                except Exception as e:
                    dataset.update_phase_status(phase.name, PhaseStatus.ERROR)
                    dataset.error_message = f"Phase {phase.name} error: {str(e)}"
                    self._publish_event("phase_error", {
                        "dataset_id": dataset.id,
                        "phase": phase.name,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break

                # Update registry
                self.registry_manager.update_dataset(dataset)

            self._publish_event("ingestion_completed", {
                "dataset_id": dataset.id,
                "ready": dataset.ready,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            dataset.error_message = f"Ingestion error: {str(e)}"
            self.registry_manager.update_dataset(dataset)
            self._publish_event("ingestion_error", {
                "dataset_id": dataset.id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

        finally:
            # Remove from running ingestions
            if dataset.id in self._running_ingestions:
                del self._running_ingestions[dataset.id]

    def _publish_event(self, event_type: str, data: dict[str, Any]):
        """Publish ingestion event."""
        try:
            self.event_manager.publish("datasets", {
                "type": event_type,
                "data": data
            })
        except Exception as e:
            print(f"Error publishing event: {e}")

    def get_running_ingestions(self) -> list[str]:
        """Get list of currently running ingestion dataset IDs."""
        return list(self._running_ingestions.keys())


# Global pipeline instance
_ingestion_pipeline: IngestionPipeline | None = None


def get_ingestion_pipeline() -> IngestionPipeline:
    """Get global ingestion pipeline instance."""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline()
    return _ingestion_pipeline
