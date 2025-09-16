"""Dataset registry management."""

import json
import os
from pathlib import Path

from .models import DatasetRecord, DatasetRegistry


class DatasetRegistryManager:
    """Manages dataset registry persistence and operations."""

    def __init__(self, registry_path: str | None = None):
        if registry_path is None:
            registry_path = os.path.join("data", "datasets", "registry.json")

        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self._registry: DatasetRegistry | None = None

    @property
    def registry(self) -> DatasetRegistry:
        """Get current registry, loading if needed."""
        if self._registry is None:
            self._registry = self.load_registry()
        return self._registry

    def load_registry(self) -> DatasetRegistry:
        """Load registry from file."""
        if not self.registry_path.exists():
            return DatasetRegistry()

        try:
            with open(self.registry_path, encoding='utf-8') as f:
                data = json.load(f)

            # Convert to DatasetRegistry model
            registry = DatasetRegistry(**data)
            return registry

        except Exception as e:
            print(f"Error loading registry: {e}")
            return DatasetRegistry()

    def save_registry(self) -> None:
        """Save registry to file."""
        if self._registry is None:
            return

        try:
            # Convert to dict for JSON serialization
            data = self._registry.model_dump(mode='json')

            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving registry: {e}")

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        """Get dataset by ID."""
        return self.registry.get_dataset(dataset_id)

    def list_datasets(self, category: str | None = None, ready: bool | None = None) -> list[DatasetRecord]:
        """List datasets with optional filtering."""
        return self.registry.filter_datasets(category=category, ready=ready)

    def update_dataset(self, dataset: DatasetRecord) -> None:
        """Update dataset in registry."""
        self.registry.add_dataset(dataset)
        self.save_registry()

    def get_dataset_path(self, dataset_id: str) -> Path:
        """Get dataset storage path."""
        return Path("data") / "datasets" / dataset_id

    def get_normalized_data_path(self, dataset_id: str) -> Path:
        """Get path to normalized data file."""
        return self.get_dataset_path(dataset_id) / "normalized" / "data.jsonl"

    def get_embeddings_path(self, dataset_id: str) -> Path:
        """Get path to embeddings directory."""
        return self.get_dataset_path(dataset_id) / "embeddings"

    def get_embeddings_vectors_path(self, dataset_id: str) -> Path:
        """Get path to embeddings vectors file."""
        return self.get_embeddings_path(dataset_id) / "vectors.json"


# Global registry instance
_registry_manager: DatasetRegistryManager | None = None


def get_registry_manager() -> DatasetRegistryManager:
    """Get global registry manager instance."""
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = DatasetRegistryManager()
    return _registry_manager
