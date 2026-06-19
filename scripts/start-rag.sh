#!/bin/bash

cd ~/local-llm/src || exit 1

source ../src/.venv/bin/activate

# optional: set huggingface offline
export HF_HUB_OFFLINE=1

echo "Starting Qdrant..."
nohup ~/local-llm/qdrant/qdrant > qdrant.log 2>&1 &

sleep 2

echo "Starting FastAPI..."
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
