"""Lightweight embeddings layer using fastembed."""

import json
import os
from pathlib import Path

import numpy as np

from .models import SearchResult
from .registry import get_registry_manager


class EmbeddingsManager:
    """Manages embedding generation and search."""

    def __init__(self):
        self.model_name = os.environ.get(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.backend = os.environ.get("EMBEDDING_BACKEND", "fastembed")
        self.max_chunk_tokens = int(os.environ.get("MAX_EMBED_CHUNK_TOKENS", "512"))

        self._model = None
        self.registry_manager = get_registry_manager()

    def _get_model(self):
        """Get or initialize embedding model."""
        if self._model is not None:
            return self._model

        try:
            if self.backend == "fastembed":
                from fastembed import TextEmbedding

                self._model = TextEmbedding(model_name=self.model_name)
            else:
                raise ValueError(f"Unsupported embedding backend: {self.backend}")
        except ImportError:
            print("fastembed not available, please install with: pip install fastembed")
            return None
        except Exception as e:
            print(f"Error initializing embedding model: {e}")
            return None

        return self._model

    def is_available(self) -> bool:
        """Check if embeddings are available."""
        return os.environ.get("ENABLE_EMBEDDINGS") == "1" and self._get_model() is not None

    def create_embeddings_for_dataset(self, dataset_id: str, normalized_file: Path) -> bool:
        """Create embeddings for a dataset."""
        if not self.is_available():
            return False

        try:
            model = self._get_model()
            if model is None:
                return False

            # Read normalized data
            texts = []
            items = []

            with open(normalized_file, encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line.strip())
                    texts.append(item["text"])
                    items.append(item)

            if not texts:
                return False

            # Generate embeddings
            embeddings = list(model.embed(texts))

            # Prepare embeddings data
            embeddings_data = {
                "model": self.model_name,
                "dimensions": len(embeddings[0]) if embeddings else 0,
                "items": [],
            }

            for item, embedding in zip(items, embeddings, strict=False):
                embeddings_data["items"].append(
                    {
                        "id": item["id"],
                        "text": item["text"],
                        "metadata": item["metadata"],
                        "vector": embedding.tolist(),
                    }
                )

            # Save embeddings
            embeddings_path = self.registry_manager.get_embeddings_path(dataset_id)
            embeddings_path.mkdir(parents=True, exist_ok=True)

            vectors_file = self.registry_manager.get_embeddings_vectors_path(dataset_id)
            with open(vectors_file, "w", encoding="utf-8") as f:
                json.dump(embeddings_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error creating embeddings for dataset {dataset_id}: {e}")
            return False

    def search_dataset(
        self, dataset_id: str, query: str, limit: int = 10, threshold: float = 0.7
    ) -> list[SearchResult]:
        """Search within a single dataset."""
        if not self.is_available():
            return []

        try:
            vectors_file = self.registry_manager.get_embeddings_vectors_path(dataset_id)
            if not vectors_file.exists():
                return []

            # Load embeddings
            with open(vectors_file, encoding="utf-8") as f:
                embeddings_data = json.load(f)

            if not embeddings_data.get("items"):
                return []

            # Generate query embedding
            model = self._get_model()
            if model is None:
                return []

            query_embedding = list(model.embed([query]))[0]

            # Calculate similarities
            results = []
            for item in embeddings_data["items"]:
                similarity = self._cosine_similarity(query_embedding, np.array(item["vector"]))

                if similarity >= threshold:
                    results.append(
                        SearchResult(
                            dataset_id=dataset_id,
                            content=item["text"],
                            score=float(similarity),
                            metadata=item["metadata"],
                        )
                    )

            # Sort by score and limit
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"Error searching dataset {dataset_id}: {e}")
            return []

    def search_multiple_datasets(
        self, dataset_ids: list[str], query: str, limit: int = 10, threshold: float = 0.7
    ) -> list[SearchResult]:
        """Search across multiple datasets."""
        all_results = []

        for dataset_id in dataset_ids:
            results = self.search_dataset(
                dataset_id, query, limit * 2, threshold
            )  # Get more results per dataset
            all_results.extend(results)

        # Sort all results by score and limit
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:limit]

    def search_all_ready_datasets(
        self, query: str, limit: int = 10, threshold: float = 0.7
    ) -> list[SearchResult]:
        """Search across all ready datasets."""
        ready_datasets = self.registry_manager.list_datasets(ready=True)
        dataset_ids = [d.id for d in ready_datasets]
        return self.search_multiple_datasets(dataset_ids, query, limit, threshold)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a.shape) == 1:
            a = a.reshape(1, -1)
        if len(b.shape) == 1:
            b = b.reshape(1, -1)

        # Compute cosine similarity
        dot_product = np.dot(a, b.T)[0, 0]
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# Global embeddings manager instance
_embeddings_manager: EmbeddingsManager | None = None


def get_embeddings_manager() -> EmbeddingsManager:
    """Get global embeddings manager instance."""
    global _embeddings_manager
    if _embeddings_manager is None:
        _embeddings_manager = EmbeddingsManager()
    return _embeddings_manager
