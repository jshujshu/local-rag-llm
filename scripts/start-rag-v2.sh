#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/src" || exit 1

source .venv/bin/activate

export HF_HUB_OFFLINE=1

echo "Starting Qdrant..."
nohup "$PROJECT_ROOT/qdrant/qdrant" > qdrant.log 2>&1 &

sleep 2

echo "Starting FastAPI..."
uvicorn api:app --host 0.0.0.0 --port 8000 --reload