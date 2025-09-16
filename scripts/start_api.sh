#!/bin/bash
# Production API runner for tRIad Terminal

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting tRIad Terminal API (Production Mode)"
echo "📂 Project root: $PROJECT_ROOT"

# Change to project directory
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

# Start the API
echo "🌟 Starting API server..."
python scripts/run_api.py
