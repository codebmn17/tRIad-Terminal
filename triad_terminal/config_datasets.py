"""Dataset configuration settings."""

import os
from typing import List


# Environment variables for dataset configuration
AUTO_DOWNLOAD_DATASETS = os.environ.get("AUTO_DOWNLOAD_DATASETS", "0") == "1"
ENABLE_EMBEDDINGS = os.environ.get("ENABLE_EMBEDDINGS", "0") == "1"
EMBEDDING_BACKEND = os.environ.get("EMBEDDING_BACKEND", "fastembed")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
MAX_EMBED_CHUNK_TOKENS = int(os.environ.get("MAX_EMBED_CHUNK_TOKENS", "512"))

# Initial datasets to auto-download
INITIAL_DATASETS: List[str] = [
    "codesearchnet_small",
    "wiki_history_events", 
    "sec_filings_sample"
]

# Override from environment if set
if os.environ.get("INITIAL_DATASETS"):
    INITIAL_DATASETS = os.environ.get("INITIAL_DATASETS", "").split(",")
    INITIAL_DATASETS = [d.strip() for d in INITIAL_DATASETS if d.strip()]