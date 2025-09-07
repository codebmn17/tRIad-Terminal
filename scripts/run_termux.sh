#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# Optional env (adjust as needed)
export AUTO_DOWNLOAD_DATASETS=${AUTO_DOWNLOAD_DATASETS:-1}
export ENABLE_EMBEDDINGS=${ENABLE_EMBEDDINGS:-0}
export TRIAD_API_TOKEN=${TRIAD_API_TOKEN:-dev-temp-token}
export TRIAD_BASE_URL=${TRIAD_BASE_URL:-http://127.0.0.1:8158}

# Ensure local imports
export PYTHONPATH=${PYTHONPATH:-$PWD}

# Auto-detect FastAPI app entrypoint (prefers api.app:app, then app:app, then api.main:app)
ENTRY=$(python - <<'PY'
import importlib, sys
candidates = [("api.app", "app"), ("app", "app"), ("api.main", "app")]
for mod, var in candidates:
    try:
        m = importlib.import_module(mod)
        if hasattr(m, var):
            print(f"{mod}:{var}")
            sys.exit(0)
    except Exception:
        pass
sys.exit(1)
PY
) || { echo "Could not locate a FastAPI application (tried api.app:app, app:app, api.main:app)."; exit 1; }

echo "Starting Uvicorn with entrypoint: $ENTRY"
python -m uvicorn "$ENTRY" --host 0.0.0.0 --port 8158
