#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/src" || exit 1

source .venv/bin/activate

# optional: set huggingface offline
export HF_HUB_OFFLINE=1

echo "Running ingestion..."
python ingest.py