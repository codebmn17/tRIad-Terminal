# Triad Terminal
#🔺️Triad Terminal🔻

A Python-first, extensible terminal environment that integrates:
- Enhanced shell and environment helpers
- Git repository management with optional GitHub integration
- Security/auth (session, password, optional biometrics groundwork)
- Voice assistant (TTS/ASR stubs and engines) and AI integration
- Theming/UI utilities and installers
- **Dataset Ingestion & Embeddings** - Real-time dataset processing with lightweight vector search

> Note: The repository currently contains multiple Version1/Version2 modules. Consolidation into a single package is planned but not part of this PR to avoid breaking changes.

## Quick start

Prerequisites: Python 3.11+ recommended (3.12 supported).

```bash
# Clone (private repo)
git clone git@github.com:codebmn17/tRIad-Terminal.git
cd tRIad-Terminal

# Optional: set up a venv and dev tools
./scripts/dev-setup.sh

# Run the main entry (one of the current entry scripts)
python triad-terminal.py
# or
python optimized_terminal.py

# Run API server with dataset management
python -c "from api.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

## Dataset Ingestion & Embeddings

The system includes a comprehensive dataset ingestion pipeline with real-time dashboard monitoring.

### Features

- **Multi-phase ingestion**: Download → Normalize → Embed (optional)
- **Real-time monitoring**: Live dashboard with SSE updates
- **Threaded processing**: Non-blocking background ingestion
- **Lightweight embeddings**: Optional vector search using fastembed
- **Auto-download**: Configurable startup ingestion
- **Category support**: Coding, history, finance datasets out of the box

### Environment Variables

```bash
# Enable auto-download of initial datasets
AUTO_DOWNLOAD_DATASETS=1

# Enable embeddings and vector search
ENABLE_EMBEDDINGS=1
EMBEDDING_BACKEND=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_EMBED_CHUNK_TOKENS=512

# Customize initial datasets (comma-separated)
INITIAL_DATASETS=codesearchnet_small,wiki_history_events,sec_filings_sample
```

### API Endpoints

- `GET /datasets/list` - List all datasets with filtering
- `POST /datasets/ingest` - Start ingestion for single dataset  
- `POST /datasets/ingest/batch` - Start batch ingestion
- `GET /datasets/status/{dataset_id}` - Get dataset status
- `GET /datasets/stream` - Server-Sent Events for real-time updates
- `POST /datasets/search` - Vector search (when embeddings enabled)
- `GET /datasets` - Interactive dashboard

### Dashboard

Access the real-time dataset management dashboard at `http://localhost:8000/datasets`:

- View all datasets with live status updates
- Monitor ingestion progress with phase-specific progress bars
- Start ingestion with one-click buttons
- Real-time log stream with SSE connection status
- Vector search interface (when embeddings enabled)

### Workflow

1. **Registry Loading**: System loads datasets from `data/datasets/registry.json`
2. **Auto-ingestion**: If `AUTO_DOWNLOAD_DATASETS=1`, starts ingesting initial datasets
3. **Phase Processing**: Each dataset goes through download→normalize→embed phases
4. **Real-time Updates**: Dashboard receives live phase progression via SSE
5. **Data Storage**: 
   - Raw data: `data/datasets/<id>/raw/`
   - Normalized: `data/datasets/<id>/normalized/data.jsonl`
   - Embeddings: `data/datasets/<id>/embeddings/vectors.json`

### Installing Embeddings Support

```bash
# Install fastembed for embeddings
pip install fastembed

# Enable embeddings
export ENABLE_EMBEDDINGS=1

# Start server - datasets will now include embedding phase
python -c "from api.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

### Future Roadmap

- Real dataset fetchers (GitHub API, Wikipedia API, SEC EDGAR)
- Queue-backed ingestion with retry logic
- Advanced vector stores (FAISS, Chroma) 
- Dataset activation for ML training dispatch
- Admin authentication and user management

## Development

- Formatting and linting: Ruff + Black (configured via pyproject.toml)
- Pre-commit hooks: see .pre-commit-config.yaml
- CI: GitHub Actions runs lint checks on push/PR

## Project layout (selected)

```
.
├── .github/workflows/         # CI workflows
├── docs/                      # Architecture and contribution docs
├── scripts/                   # Dev helper scripts
├── *.py                       # Existing Python modules (Version1/Version2 coexist)
├── *.js, *.sh                 # Installer/runner helpers
└── README.md
```

## Roadmap (proposed)
- Package under src/triad_terminal/ with typed modules
- Single, canonical implementations (remove Version* duplicates)
- Add tests and coverage gates in CI
- Optional releases and packaging if distribution is desired
=======
## Web browsing (Brave preferred)

We ship a small helper that prefers Brave Browser if installed and falls back to the system default. See docs/BRAVE.md for installation instructions.

```python
from utils.browser import open_url
open_url("https://example.com")
```

## Converting .docx artifacts

If you see files like `main.py.docx` or `devenv.js.docx`, use the converter to generate proper source files while keeping the originals:

```bash
pip install -r requirements-dev.txt
python tools/convert_docx.py
```

See docs/CONVERSION.md for details.

## Performance Baseline

Triad Terminal includes built-in performance instrumentation to help measure and optimize performance. See [docs/performance_baseline.md](docs/performance_baseline.md) for detailed instructions on gathering baseline metrics.

**Quick start:**
```bash
# Enable performance logging
export TRIAD_PERF=1

# Run with timing
time python triad-terminal.py --help

# Check performance summary in terminal
/perf
```

## Development

- Formatting and linting: Ruff + Black (configured via pyproject.toml)
- Pre-commit hooks: see .pre-commit-config.yaml
- CI: GitHub Actions runs lint checks on push/PR
